"""NumPy .npy writer and loader for embedding storage.

Stores embeddings and candidate IDs as separate .npy files,
compatible with downstream FAISS/Qdrant ingestion pipelines.
"""

import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


def save_embeddings(
    vectors: np.ndarray,
    candidate_ids: list[str],
    output_dir: Path,
) -> tuple[Path, Path]:
    """Save embeddings and candidate IDs to .npy files.

    Creates the output directory if it does not exist.
    Writes two files:
        - embeddings.npy: float32 array of shape (N, D)
        - candidate_ids.npy: Unicode string array of shape (N,)

    Args:
        vectors: Embedding matrix of shape (N, D), dtype float32.
        candidate_ids: List of candidate ID strings, length N.
        output_dir: Directory to write output files.

    Returns:
        Tuple of (embeddings_path, ids_path).

    Raises:
        ValueError: If vectors and candidate_ids have mismatched lengths.
    """
    if vectors.shape[0] != len(candidate_ids):
        raise ValueError(
            f"Shape mismatch: {vectors.shape[0]} vectors vs "
            f"{len(candidate_ids)} candidate IDs."
        )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    embeddings_path = output_dir / "embeddings.npy"
    ids_path = output_dir / "candidate_ids.npy"

    # Ensure float32 before saving.
    vectors = vectors.astype(np.float32)

    np.save(embeddings_path, vectors)
    logger.info(
        "Saved embeddings: %s (shape=%s, dtype=%s, size=%.1f MB)",
        embeddings_path,
        vectors.shape,
        vectors.dtype,
        vectors.nbytes / (1024 * 1024),
    )

    ids_array = np.array(candidate_ids, dtype=str)
    np.save(ids_path, ids_array)
    logger.info(
        "Saved candidate IDs: %s (count=%d)",
        ids_path,
        len(candidate_ids),
    )

    return embeddings_path, ids_path


def load_embeddings(output_dir: Path) -> tuple[np.ndarray, np.ndarray]:
    """Load embeddings and candidate IDs from .npy files.

    Args:
        output_dir: Directory containing embeddings.npy and candidate_ids.npy.

    Returns:
        Tuple of (embeddings_array, candidate_ids_array).

    Raises:
        FileNotFoundError: If either .npy file is missing.
        ValueError: If the arrays have mismatched first dimensions.
    """
    output_dir = Path(output_dir)

    embeddings_path = output_dir / "embeddings.npy"
    ids_path = output_dir / "candidate_ids.npy"

    if not embeddings_path.exists():
        raise FileNotFoundError(f"Embeddings file not found: {embeddings_path}")
    if not ids_path.exists():
        raise FileNotFoundError(f"Candidate IDs file not found: {ids_path}")

    vectors = np.load(embeddings_path)
    candidate_ids = np.load(ids_path)

    if vectors.shape[0] != candidate_ids.shape[0]:
        raise ValueError(
            f"Alignment mismatch: {vectors.shape[0]} embeddings vs "
            f"{candidate_ids.shape[0]} candidate IDs."
        )

    logger.info(
        "Loaded embeddings: shape=%s | candidate IDs: count=%d",
        vectors.shape,
        candidate_ids.shape[0],
    )

    return vectors, candidate_ids
