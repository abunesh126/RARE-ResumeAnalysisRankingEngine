"""Batch checkpoint manager for crash-resilient pipeline runs.

Saves intermediate embeddings and candidate IDs after every checkpoint
interval so that a crashed or interrupted run can be resumed without
reprocessing already-embedded records.

Checkpoint layout::

    output_dir/
    └── checkpoints/
        ├── batch_001.npz
        ├── batch_002.npz
        └── checkpoint_state.json
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import orjson

logger = logging.getLogger(__name__)


@dataclass
class CheckpointState:
    """Snapshot of pipeline progress at the last completed checkpoint."""

    last_batch: int
    records_processed: int
    input_path: str
    batches: list[str] = field(default_factory=list)


class CheckpointManager:
    """Manages batch checkpoints for crash recovery.

    Args:
        output_dir: Root output directory. Checkpoints are stored in
            ``output_dir/checkpoints/``.
    """

    _STATE_FILE = "checkpoint_state.json"

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = Path(output_dir)
        self._checkpoint_dir = self._output_dir / "checkpoints"
        self._checkpoint_dir.mkdir(parents=True, exist_ok=True)

    @property
    def checkpoint_dir(self) -> Path:
        """Return the checkpoint directory path."""
        return self._checkpoint_dir

    # ── Save ──────────────────────────────────────────────────────

    def save_checkpoint(
        self,
        batch_idx: int,
        embeddings: np.ndarray,
        candidate_ids: list[str],
        input_path: str,
        records_processed: int,
    ) -> Path:
        """Persist a batch checkpoint to disk.

        Args:
            batch_idx: 1-based batch ordinal.
            embeddings: Embedding matrix for this batch, shape ``(B, D)``.
            candidate_ids: Candidate ID strings for this batch.
            input_path: Original JSONL input path (for resume validation).
            records_processed: Cumulative records processed including this batch.

        Returns:
            Path to the saved ``.npz`` file.
        """
        batch_name = f"batch_{batch_idx:04d}.npz"
        batch_path = self._checkpoint_dir / batch_name

        np.savez_compressed(
            batch_path,
            embeddings=embeddings.astype(np.float32),
            candidate_ids=np.array(candidate_ids, dtype=str),
        )

        # Update state file.
        state = self._load_state_raw()
        state["last_batch"] = batch_idx
        state["records_processed"] = records_processed
        state["input_path"] = input_path
        if batch_name not in state.get("batches", []):
            state.setdefault("batches", []).append(batch_name)
        self._write_state(state)

        logger.info(
            "Checkpoint saved: %s (%d records so far)",
            batch_name,
            records_processed,
        )
        return batch_path

    # ── Load ──────────────────────────────────────────────────────

    def load_checkpoint(self) -> CheckpointState | None:
        """Load the most recent checkpoint state.

        Returns:
            A ``CheckpointState`` if a valid checkpoint exists, else ``None``.
        """
        state_path = self._checkpoint_dir / self._STATE_FILE
        if not state_path.exists():
            logger.info("No checkpoint found in %s", self._checkpoint_dir)
            return None

        raw = orjson.loads(state_path.read_bytes())
        state = CheckpointState(
            last_batch=raw["last_batch"],
            records_processed=raw["records_processed"],
            input_path=raw["input_path"],
            batches=raw.get("batches", []),
        )
        logger.info(
            "Loaded checkpoint: %d batches, %d records processed.",
            state.last_batch,
            state.records_processed,
        )
        return state

    def load_batch_data(
        self,
        state: CheckpointState,
    ) -> tuple[list[np.ndarray], list[str]]:
        """Load all checkpoint batch arrays.

        Args:
            state: Checkpoint state from ``load_checkpoint()``.

        Returns:
            Tuple of (list of embedding arrays, flat list of candidate IDs).
        """
        all_embeddings: list[np.ndarray] = []
        all_ids: list[str] = []

        for batch_name in sorted(state.batches):
            batch_path = self._checkpoint_dir / batch_name
            if not batch_path.exists():
                logger.warning("Missing checkpoint batch file: %s", batch_path)
                continue
            data = np.load(batch_path)
            all_embeddings.append(data["embeddings"])
            all_ids.extend(data["candidate_ids"].tolist())

        logger.info(
            "Loaded %d checkpoint batches (%d total records).",
            len(all_embeddings),
            len(all_ids),
        )
        return all_embeddings, all_ids

    # ── Cleanup ───────────────────────────────────────────────────

    def clear_checkpoints(self) -> None:
        """Remove all checkpoint files and the state file."""
        for f in self._checkpoint_dir.iterdir():
            f.unlink()
        logger.info("Cleared all checkpoints in %s", self._checkpoint_dir)

    # ── Internal ──────────────────────────────────────────────────

    def _load_state_raw(self) -> dict:
        """Load raw state dict, or return empty dict."""
        state_path = self._checkpoint_dir / self._STATE_FILE
        if state_path.exists():
            return dict(orjson.loads(state_path.read_bytes()))
        return {}

    def _write_state(self, state: dict) -> None:
        """Write state dict to JSON."""
        state_path = self._checkpoint_dir / self._STATE_FILE
        state_path.write_bytes(
            orjson.dumps(state, option=orjson.OPT_INDENT_2)
        )
