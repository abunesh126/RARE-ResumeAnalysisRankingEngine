"""Tests for normalizer module."""

import numpy as np
import pytest

from resume_embedding.app.model import l2_normalize, validate_embeddings


class TestL2Normalize:
    """Tests for the l2_normalize function."""

    def test_normalizes_to_unit_norm(self) -> None:
        """Normalized vectors should have L2 norm ~1.0."""
        vectors = np.array([[3.0, 4.0, 0.0]], dtype=np.float32)
        normalized = l2_normalize(vectors)
        norm = np.linalg.norm(normalized[0])
        assert abs(norm - 1.0) < 1e-6

    def test_batch_normalization(self) -> None:
        """Batch of vectors should all have unit norm."""
        rng = np.random.default_rng(42)
        vectors = rng.standard_normal((100, 384)).astype(np.float32)
        normalized = l2_normalize(vectors)
        norms = np.linalg.norm(normalized, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-6)

    def test_preserves_shape(self) -> None:
        """Output shape should match input shape."""
        vectors = np.ones((5, 384), dtype=np.float32)
        normalized = l2_normalize(vectors)
        assert normalized.shape == (5, 384)

    def test_preserves_dtype(self) -> None:
        """Output dtype should be float32."""
        vectors = np.ones((3, 384), dtype=np.float64)
        normalized = l2_normalize(vectors)
        assert normalized.dtype == np.float32

    def test_zero_vector_handling(self) -> None:
        """Zero vectors should remain zero (no division by zero)."""
        vectors = np.array([
            [1.0, 2.0, 3.0],
            [0.0, 0.0, 0.0],
            [4.0, 5.0, 6.0],
        ], dtype=np.float32)
        normalized = l2_normalize(vectors)
        assert np.allclose(normalized[1], [0.0, 0.0, 0.0])
        assert abs(np.linalg.norm(normalized[0]) - 1.0) < 1e-6
        assert abs(np.linalg.norm(normalized[2]) - 1.0) < 1e-6

    def test_1d_array_raises(self) -> None:
        """1D array should raise ValueError."""
        with pytest.raises(ValueError, match="2D"):
            l2_normalize(np.array([1.0, 2.0, 3.0]))

    def test_already_normalized_is_idempotent(self) -> None:
        """Re-normalizing an already normalized vector should be idempotent."""
        vectors = np.array([[0.6, 0.8, 0.0]], dtype=np.float32)
        first = l2_normalize(vectors)
        second = l2_normalize(first)
        assert np.allclose(first, second, atol=1e-7)


class TestValidateEmbeddings:
    """Tests for the validate_embeddings function."""

    def test_valid_embeddings_pass(self, sample_embeddings: np.ndarray) -> None:
        """Properly normalized 384-dim embeddings should pass validation."""
        assert validate_embeddings(sample_embeddings) is True

    def test_wrong_dimension_fails(self) -> None:
        """Wrong dimension should raise ValueError."""
        vectors = np.ones((3, 128), dtype=np.float32)
        vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
        with pytest.raises(ValueError, match="Expected dimension 384"):
            validate_embeddings(vectors)

    def test_wrong_dtype_fails(self) -> None:
        """Wrong dtype should raise ValueError."""
        rng = np.random.default_rng(42)
        vectors = rng.standard_normal((3, 384))
        vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
        with pytest.raises(ValueError, match="float32"):
            validate_embeddings(vectors)

    def test_non_normalized_fails(self) -> None:
        """Non-normalized vectors should raise ValueError."""
        vectors = np.ones((3, 384), dtype=np.float32) * 5.0
        with pytest.raises(ValueError, match="not L2-normalized"):
            validate_embeddings(vectors)

    def test_1d_fails(self) -> None:
        """1D array should raise ValueError."""
        with pytest.raises(ValueError, match="2D"):
            validate_embeddings(np.array([1.0], dtype=np.float32))

    def test_custom_dimension(self) -> None:
        """Custom dimension parameter should work."""
        rng = np.random.default_rng(42)
        vectors = rng.standard_normal((3, 128)).astype(np.float32)
        vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
        assert validate_embeddings(vectors, dimension=128) is True
