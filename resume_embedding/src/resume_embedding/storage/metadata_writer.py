"""Metadata JSON writer for embedding artifacts.

Writes a metadata.json file alongside the .npy files to document
the model, dimension, normalization status, device, and candidate count.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

import orjson

logger = logging.getLogger(__name__)


def write_metadata(
    output_dir: Path,
    *,
    model: str,
    dimension: int,
    normalized: bool,
    records_processed: int,
    device: str = "cpu",
    input_file: str = "",
) -> Path:
    """Write embedding metadata to a JSON file.

    Creates a metadata.json file in the output directory with
    information about the generated embeddings.

    Args:
        output_dir: Directory to write metadata.json.
        model: HuggingFace model identifier used for embedding.
        dimension: Dimensionality of the embedding vectors.
        normalized: Whether vectors are L2-normalized.
        records_processed: Total number of candidates embedded.
        device: Compute device used ('cuda' or 'cpu').
        input_file: Path to the source JSONL file.

    Returns:
        Path to the written metadata.json file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "model": model,
        "dimension": dimension,
        "normalized": normalized,
        "device": device,
        "records_processed": records_processed,
        "input_file": input_file,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }

    metadata_path = output_dir / "metadata.json"

    with open(metadata_path, "wb") as fh:
        fh.write(orjson.dumps(metadata, option=orjson.OPT_INDENT_2))

    logger.info("Wrote metadata: %s", metadata_path)

    return metadata_path
