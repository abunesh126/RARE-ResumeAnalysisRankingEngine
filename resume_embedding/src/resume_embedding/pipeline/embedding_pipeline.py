"""Embedding pipeline orchestrator.

Coordinates the full pipeline: JSONL streaming → parsing → text building
→ batch embedding → L2 normalization → checkpoint → NPY storage → metadata.

Supports:
- Direct JSONL file input (no hardcoded paths)
- Batch checkpointing with crash recovery (--resume)
- Device awareness (auto/cuda/cpu)
- File logging to outputs/logs/

Designed for memory efficiency with 100,000+ candidate datasets.
"""

import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from tqdm import tqdm

from resume_embedding.config.settings import PipelineSettings, DEFAULT_SETTINGS
from resume_embedding.embedding.embedder import generate_embeddings
from resume_embedding.embedding.normalizer import l2_normalize, validate_embeddings
from resume_embedding.formatter.text_builder import candidate_to_text
from resume_embedding.parser.candidate_parser import load_candidates
from resume_embedding.pipeline.checkpoint import CheckpointManager
from resume_embedding.storage.metadata_writer import write_metadata
from resume_embedding.storage.npy_writer import save_embeddings

logger = logging.getLogger(__name__)


def _count_records(file_path: Path) -> int:
    """Count records in a JSONL or JSON file for progress bar estimation.

    Args:
        file_path: Path to the input file (.jsonl or .json).

    Returns:
        Number of records in the file.
    """
    if file_path.suffix.lower() == ".json":
        import orjson
        data = orjson.loads(file_path.read_bytes())
        return len(data) if isinstance(data, list) else 1

    # JSONL: count non-empty lines.
    count = 0
    with open(file_path, "rb") as fh:
        for line in fh:
            if line.strip():
                count += 1
    return count


def _setup_file_logging(output_dir: Path) -> logging.FileHandler:
    """Add a file handler to the root logger.

    Logs are written to ``output_dir/logs/run_YYYYMMDD_HHMMSS.log``.

    Args:
        output_dir: Root output directory.

    Returns:
        The configured FileHandler (for cleanup if needed).
    """
    log_dir = output_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"run_{timestamp}.log"

    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logging.getLogger().addHandler(handler)
    logger.info("File logging enabled: %s", log_path)
    return handler


def run_pipeline(
    input_path: str | Path,
    output_path: str | Path | None = None,
    *,
    batch_size: int | None = None,
    device: str | None = None,
    resume: bool = False,
    settings: PipelineSettings | None = None,
) -> dict[str, object]:
    """Execute the full embedding generation pipeline.

    Streams candidate records from a JSONL file, converts to structured text,
    generates embeddings in batches, normalizes, checkpoints, and writes to
    .npy files.

    Args:
        input_path: Path to the candidates JSONL file.
        output_path: Directory for output artifacts.
            Falls back to ``./outputs`` if None.
        batch_size: Embedding batch size.
            Falls back to ``settings.default_batch_size`` if None.
        device: Compute device ('auto', 'cuda', 'cpu').
            Falls back to ``settings.device`` if None.
        resume: If True, resume from the last checkpoint in ``output_path``.
        settings: Pipeline configuration. Uses DEFAULT_SETTINGS if None.

    Returns:
        Dictionary with pipeline execution metadata::

            {
                "total_candidates": int,
                "embeddings_shape": tuple,
                "output_dir": str,
                "elapsed_seconds": float,
                "device": str,
            }

    Raises:
        FileNotFoundError: If the JSONL file does not exist.
        ValueError: If validation fails after embedding or no candidates are found.
    """
    if settings is None:
        settings = DEFAULT_SETTINGS

    resolved_input = Path(input_path)
    resolved_batch_size = batch_size if batch_size is not None else settings.default_batch_size
    resolved_device = device if device is not None else settings.device

    # Resolve output directory — auto-generate a timestamped folder when not specified.
    if output_path:
        resolved_output = Path(output_path)
    else:
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        resolved_output = Path("./outputs") / f"run_{timestamp}"

    # Resolve auto device.
    if resolved_device == "auto":
        resolved_device = settings.resolve_device()

    # Set up file logging.
    file_handler = _setup_file_logging(resolved_output)

    # Checkpoint manager.
    ckpt = CheckpointManager(resolved_output)

    # ── Resume handling ───────────────────────────────────────────
    all_embeddings: list[np.ndarray] = []
    all_candidate_ids: list[str] = []
    skip_records = 0
    batch_count = 0

    if resume:
        state = ckpt.load_checkpoint()
        if state is not None:
            logger.info(
                "Resuming from checkpoint: %d batches, %d records already processed.",
                state.last_batch,
                state.records_processed,
            )
            prev_embeddings, prev_ids = ckpt.load_batch_data(state)
            all_embeddings.extend(prev_embeddings)
            all_candidate_ids.extend(prev_ids)
            skip_records = state.records_processed
            batch_count = state.last_batch

            # Use the input path from the checkpoint if not explicitly provided.
            if str(resolved_input) == "." or not resolved_input.exists():
                resolved_input = Path(state.input_path)
        else:
            logger.info("No checkpoint found. Starting from the beginning.")

    # ── Validate input ────────────────────────────────────────────
    if not resolved_input.exists():
        raise FileNotFoundError(f"Input file not found: {resolved_input}")

    logger.info("=" * 60)
    logger.info("RESUME EMBEDDING PIPELINE")
    logger.info("=" * 60)
    logger.info("Input:      %s", resolved_input)
    logger.info("Output:     %s", resolved_output)
    logger.info("Model:      %s", settings.model_name)
    logger.info("Dimension:  %d", settings.vector_dimension)
    logger.info("Batch size: %d", resolved_batch_size)
    logger.info("Device:     %s", resolved_device)
    logger.info("Checkpoint: every %d records", settings.checkpoint_interval)
    if skip_records > 0:
        logger.info("Resuming:   skipping first %d records", skip_records)
    logger.info("=" * 60)

    start_time = time.perf_counter()

    # Phase 1: Count lines for progress estimation.
    logger.info("Counting records...")
    total_records = _count_records(resolved_input)
    logger.info("Found %d records in %s", total_records, resolved_input.name)

    # Phase 2: Stream, parse, build text, embed in batches.
    text_batch: list[str] = []
    id_batch: list[str] = []
    processed = len(all_candidate_ids)
    records_seen = 0

    candidates = load_candidates(resolved_input, skip_invalid=True)
    progress = tqdm(
        candidates,
        total=total_records,
        desc="Processing candidates",
        unit="candidate",
        initial=skip_records,
    )

    for candidate in progress:
        records_seen += 1

        # Skip already-checkpointed records.
        if records_seen <= skip_records:
            continue

        text = candidate_to_text(candidate)
        text_batch.append(text)
        id_batch.append(candidate.candidate_id)

        if len(text_batch) >= resolved_batch_size:
            batch_count += 1
            embeddings = generate_embeddings(
                text_batch,
                model_name=settings.model_name,
                batch_size=resolved_batch_size,
            )
            normalized = l2_normalize(embeddings)
            all_embeddings.append(normalized)
            all_candidate_ids.extend(id_batch)
            processed += len(text_batch)

            # Save checkpoint at configured interval.
            if processed % settings.checkpoint_interval < resolved_batch_size:
                ckpt.save_checkpoint(
                    batch_idx=batch_count,
                    embeddings=normalized,
                    candidate_ids=id_batch,
                    input_path=str(resolved_input),
                    records_processed=processed,
                )

            text_batch.clear()
            id_batch.clear()

            progress.set_postfix(
                batches=batch_count,
                embedded=processed,
            )

    # Handle remaining texts in the last partial batch.
    if text_batch:
        batch_count += 1
        embeddings = generate_embeddings(
            text_batch,
            model_name=settings.model_name,
            batch_size=resolved_batch_size,
        )
        normalized = l2_normalize(embeddings)
        all_embeddings.append(normalized)
        all_candidate_ids.extend(id_batch)
        processed += len(text_batch)

        # Final checkpoint for the last batch.
        ckpt.save_checkpoint(
            batch_idx=batch_count,
            embeddings=normalized,
            candidate_ids=id_batch,
            input_path=str(resolved_input),
            records_processed=processed,
        )

    progress.close()

    if processed == 0:
        raise ValueError("No candidates were processed. Check the dataset file.")

    # Phase 3: Stack all embeddings into a single array.
    logger.info("Stacking %d batches into final array...", batch_count)
    final_embeddings = np.vstack(all_embeddings)
    logger.info("Final embeddings shape: %s", final_embeddings.shape)

    # Phase 4: Validate.
    logger.info("Validating embeddings...")
    validate_embeddings(
        final_embeddings,
        dimension=settings.vector_dimension,
        tolerance=settings.norm_tolerance,
    )

    # Phase 5: Save outputs.
    logger.info("Saving outputs to %s", resolved_output)
    save_embeddings(
        final_embeddings,
        all_candidate_ids,
        resolved_output,
    )
    write_metadata(
        resolved_output,
        model=settings.model_name,
        dimension=settings.vector_dimension,
        normalized=True,
        records_processed=processed,
        device=resolved_device,
        input_file=str(resolved_input),
    )

    # Phase 6: Clean up checkpoints on success.
    logger.info("Cleaning up checkpoints...")
    ckpt.clear_checkpoints()

    elapsed = time.perf_counter() - start_time

    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETE")
    logger.info("Candidates processed: %d", processed)
    logger.info("Embeddings shape:     %s", final_embeddings.shape)
    logger.info("Device:               %s", resolved_device)
    logger.info("Elapsed time:         %.1f seconds", elapsed)
    logger.info("Throughput:           %.1f candidates/sec", processed / elapsed if elapsed > 0 else 0)
    logger.info("Output directory:     %s", resolved_output)
    logger.info("=" * 60)

    # Remove file handler to avoid leaking handles.
    logging.getLogger().removeHandler(file_handler)
    file_handler.close()

    return {
        "total_candidates": processed,
        "embeddings_shape": final_embeddings.shape,
        "output_dir": str(resolved_output),
        "elapsed_seconds": round(elapsed, 2),
        "device": resolved_device,
    }
