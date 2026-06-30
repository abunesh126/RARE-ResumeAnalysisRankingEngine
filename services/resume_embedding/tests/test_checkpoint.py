"""Tests for the CheckpointManager."""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from resume_embedding.app.io import CheckpointManager


@pytest.fixture
def output_dir() -> Path:
    """Create a temporary output directory."""
    return Path(tempfile.mkdtemp(prefix="ckpt_test_"))


@pytest.fixture
def ckpt(output_dir: Path) -> CheckpointManager:
    """Create a CheckpointManager with a temp output dir."""
    return CheckpointManager(output_dir)


@pytest.fixture
def sample_batch() -> tuple[np.ndarray, list[str]]:
    """Return a small batch of embeddings and IDs."""
    rng = np.random.default_rng(42)
    embeddings = rng.standard_normal((5, 384)).astype(np.float32)
    ids = [f"CAND_{i:07d}" for i in range(1, 6)]
    return embeddings, ids


class TestCheckpointManager:
    """Tests for checkpoint save/load/clear."""

    def test_no_checkpoint_returns_none(self, ckpt: CheckpointManager) -> None:
        """load_checkpoint should return None when no checkpoints exist."""
        assert ckpt.load_checkpoint() is None

    def test_save_and_load_checkpoint(
        self, ckpt: CheckpointManager, sample_batch: tuple
    ) -> None:
        """Should save and reload a checkpoint correctly."""
        embeddings, ids = sample_batch

        ckpt.save_checkpoint(
            batch_idx=1,
            embeddings=embeddings,
            candidate_ids=ids,
            input_path="/path/to/data.jsonl",
            records_processed=5,
        )

        state = ckpt.load_checkpoint()
        assert state is not None
        assert state.last_batch == 1
        assert state.records_processed == 5
        assert state.input_path == "/path/to/data.jsonl"
        assert len(state.batches) == 1

    def test_save_multiple_batches(
        self, ckpt: CheckpointManager, sample_batch: tuple
    ) -> None:
        """Should track multiple batch files."""
        embeddings, ids = sample_batch

        ckpt.save_checkpoint(
            batch_idx=1, embeddings=embeddings, candidate_ids=ids,
            input_path="/data.jsonl", records_processed=5,
        )
        ckpt.save_checkpoint(
            batch_idx=2, embeddings=embeddings, candidate_ids=ids,
            input_path="/data.jsonl", records_processed=10,
        )

        state = ckpt.load_checkpoint()
        assert state is not None
        assert state.last_batch == 2
        assert state.records_processed == 10
        assert len(state.batches) == 2

    def test_load_batch_data(
        self, ckpt: CheckpointManager, sample_batch: tuple
    ) -> None:
        """Should load all batch embeddings and IDs."""
        embeddings, ids = sample_batch

        ckpt.save_checkpoint(
            batch_idx=1, embeddings=embeddings, candidate_ids=ids,
            input_path="/data.jsonl", records_processed=5,
        )
        ckpt.save_checkpoint(
            batch_idx=2, embeddings=embeddings, candidate_ids=ids,
            input_path="/data.jsonl", records_processed=10,
        )

        state = ckpt.load_checkpoint()
        loaded_embeddings, loaded_ids = ckpt.load_batch_data(state)

        assert len(loaded_embeddings) == 2
        assert len(loaded_ids) == 10  # 5 + 5
        assert loaded_embeddings[0].shape == (5, 384)

    def test_clear_checkpoints(
        self, ckpt: CheckpointManager, sample_batch: tuple
    ) -> None:
        """Should remove all checkpoint files."""
        embeddings, ids = sample_batch

        ckpt.save_checkpoint(
            batch_idx=1, embeddings=embeddings, candidate_ids=ids,
            input_path="/data.jsonl", records_processed=5,
        )

        ckpt.clear_checkpoints()

        assert ckpt.load_checkpoint() is None
        remaining = list(ckpt.checkpoint_dir.iterdir())
        assert len(remaining) == 0

    def test_checkpoint_dir_created(self, output_dir: Path) -> None:
        """Checkpoint directory should be created automatically."""
        ckpt = CheckpointManager(output_dir)
        assert ckpt.checkpoint_dir.exists()
        assert ckpt.checkpoint_dir == output_dir / "checkpoints"

    def test_embeddings_dtype_preserved(
        self, ckpt: CheckpointManager, sample_batch: tuple
    ) -> None:
        """Saved embeddings should be float32."""
        embeddings, ids = sample_batch

        ckpt.save_checkpoint(
            batch_idx=1, embeddings=embeddings, candidate_ids=ids,
            input_path="/data.jsonl", records_processed=5,
        )

        state = ckpt.load_checkpoint()
        loaded_embeddings, _ = ckpt.load_batch_data(state)
        assert loaded_embeddings[0].dtype == np.float32
