"""Storage writers."""

from resume_embedding.storage.npy_writer import save_embeddings, load_embeddings
from resume_embedding.storage.metadata_writer import write_metadata

__all__ = ["save_embeddings", "load_embeddings", "write_metadata"]
