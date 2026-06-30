"""Tests for embedder module."""

import numpy as np
import pytest

from resume_embedding.app.model import generate_embeddings


class TestGenerateEmbeddings:
    """Tests for the generate_embeddings function."""

    def test_single_text_embedding(self) -> None:
        """Single text should produce (1, 384) embedding."""
        result = generate_embeddings(["Hello world"])
        assert isinstance(result, np.ndarray)
        assert result.shape == (1, 384)
        assert result.dtype == np.float32

    def test_batch_embedding(self) -> None:
        """Batch of texts should produce (N, 384) embeddings."""
        texts = [
            "Senior Python Developer with 5 years experience",
            "Data Scientist specializing in NLP",
            "Frontend Engineer with React expertise",
        ]
        result = generate_embeddings(texts)
        assert result.shape == (3, 384)
        assert result.dtype == np.float32

    def test_empty_texts_raises(self) -> None:
        """Empty text list should raise ValueError."""
        with pytest.raises(ValueError, match="empty"):
            generate_embeddings([])

    def test_different_texts_produce_different_embeddings(self) -> None:
        """Semantically different texts should produce different embeddings."""
        texts = [
            "Machine Learning Engineer with PyTorch",
            "Certified Accountant with tax expertise",
        ]
        result = generate_embeddings(texts)
        similarity = np.dot(result[0], result[1])
        # These are very different, so cosine similarity should be relatively low
        assert similarity < 0.95

    def test_custom_batch_size(self) -> None:
        """Custom batch size should work without errors."""
        texts = [f"Sample text number {i}" for i in range(10)]
        result = generate_embeddings(texts, batch_size=3)
        assert result.shape == (10, 384)

    def test_embedding_values_finite(self) -> None:
        """All embedding values should be finite (no NaN/Inf)."""
        result = generate_embeddings(["Test embedding values"])
        assert np.all(np.isfinite(result))
