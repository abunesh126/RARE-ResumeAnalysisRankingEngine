"""Embedding generation and normalization."""

from resume_embedding.embedding.embedder import generate_embeddings
from resume_embedding.embedding.normalizer import l2_normalize, validate_embeddings

__all__ = ["generate_embeddings", "l2_normalize", "validate_embeddings"]
