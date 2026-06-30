"""Storage and retrieval layer for candidate ingestion and vector search."""

from .config import (
    EMBEDDING_MODEL_NAME,
    KEYWORD_WEIGHT,
    OVERFETCH_FACTOR,
    QDRANT_COLLECTION_NAME,
    QDRANT_HOST,
    QDRANT_PORT,
    VECTOR_WEIGHT,
)
from .qdrant_setup import setup_qdrant
from .retrieval import ResumeRetriever

__all__ = [
    "EMBEDDING_MODEL_NAME",
    "KEYWORD_WEIGHT",
    "OVERFETCH_FACTOR",
    "QDRANT_COLLECTION_NAME",
    "QDRANT_HOST",
    "QDRANT_PORT",
    "VECTOR_WEIGHT",
    "ResumeRetriever",
    "setup_qdrant",
]
