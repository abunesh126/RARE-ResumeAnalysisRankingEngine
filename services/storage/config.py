"""Shared configuration for the storage and retrieval module."""

QDRANT_COLLECTION_NAME = "resumes"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333

EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"

VECTOR_WEIGHT = 0.7
KEYWORD_WEIGHT = 0.3
OVERFETCH_FACTOR = 3

assert 0 <= VECTOR_WEIGHT <= 1
assert 0 <= KEYWORD_WEIGHT <= 1
assert abs((VECTOR_WEIGHT + KEYWORD_WEIGHT) - 1.0) < 1e-6
