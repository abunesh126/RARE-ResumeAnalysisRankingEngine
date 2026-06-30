"""Tests for npy_writer module."""

from pathlib import Path

import numpy as np
import pytest

from resume_embedding.app.io import load_embeddings, save_embeddings


class TestSaveEmbeddings:
    """Tests for the save_embeddings function."""

    def test_save_creates_files(
        self,
        sample_embeddings: np.ndarray,
        sample_candidate_ids: list[str],
        tmp_output_dir: Path,
    ) -> None:
        """save_embeddings should create both .npy files."""
        emb_path, ids_path = save_embeddings(
            sample_embeddings, sample_candidate_ids, tmp_output_dir
        )
        assert emb_path.exists()
        assert ids_path.exists()
        assert emb_path.name == "embeddings.npy"
        assert ids_path.name == "candidate_ids.npy"

    def test_saved_embeddings_shape(
        self,
        sample_embeddings: np.ndarray,
        sample_candidate_ids: list[str],
        tmp_output_dir: Path,
    ) -> None:
        """Saved embeddings should have the correct shape."""
        save_embeddings(sample_embeddings, sample_candidate_ids, tmp_output_dir)
        loaded = np.load(tmp_output_dir / "embeddings.npy")
        assert loaded.shape == sample_embeddings.shape
        assert loaded.dtype == np.float32

    def test_saved_ids_content(
        self,
        sample_embeddings: np.ndarray,
        sample_candidate_ids: list[str],
        tmp_output_dir: Path,
    ) -> None:
        """Saved candidate IDs should match input."""
        save_embeddings(sample_embeddings, sample_candidate_ids, tmp_output_dir)
        loaded_ids = np.load(tmp_output_dir / "candidate_ids.npy")
        assert list(loaded_ids) == sample_candidate_ids

    def test_shape_mismatch_raises(self, tmp_output_dir: Path) -> None:
        """Mismatched vectors and IDs should raise ValueError."""
        vectors = np.ones((5, 384), dtype=np.float32)
        ids = ["CAND_0000001", "CAND_0000002"]  # Only 2 IDs for 5 vectors
        with pytest.raises(ValueError, match="Shape mismatch"):
            save_embeddings(vectors, ids, tmp_output_dir)

    def test_creates_output_dir(
        self,
        sample_embeddings: np.ndarray,
        sample_candidate_ids: list[str],
        tmp_output_dir: Path,
    ) -> None:
        """Should create the output directory if it doesn't exist."""
        nested_dir = tmp_output_dir / "nested" / "deep"
        save_embeddings(sample_embeddings, sample_candidate_ids, nested_dir)
        assert nested_dir.exists()
        assert (nested_dir / "embeddings.npy").exists()


class TestLoadEmbeddings:
    """Tests for the load_embeddings function."""

    def test_load_roundtrip(
        self,
        sample_embeddings: np.ndarray,
        sample_candidate_ids: list[str],
        tmp_output_dir: Path,
    ) -> None:
        """Save then load should return identical data."""
        save_embeddings(sample_embeddings, sample_candidate_ids, tmp_output_dir)
        loaded_vectors, loaded_ids = load_embeddings(tmp_output_dir)
        assert np.allclose(loaded_vectors, sample_embeddings)
        assert list(loaded_ids) == sample_candidate_ids

    def test_missing_embeddings_file(self, tmp_output_dir: Path) -> None:
        """Missing embeddings.npy should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="embeddings"):
            load_embeddings(tmp_output_dir)

    def test_missing_ids_file(self, tmp_output_dir: Path) -> None:
        """Missing candidate_ids.npy should raise FileNotFoundError."""
        np.save(tmp_output_dir / "embeddings.npy", np.ones((3, 384), dtype=np.float32))
        with pytest.raises(FileNotFoundError, match="candidate_ids"):
            load_embeddings(tmp_output_dir)
