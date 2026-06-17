"""L2 normalization and embedding validation.

Provides functions to normalize embedding vectors to unit L2 norm
and to validate that embeddings meet dimensional and normalization requirements.
"""

import logging

import numpy as np

from resume_embedding.config.settings import DEFAULT_SETTINGS

logger = logging.getLogger(__name__)


def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    """Normalize each row vector to unit L2 norm.

    Handles zero-norm vectors gracefully by leaving them as zero vectors.

    Args:
        vectors: NumPy array of shape (N, D) with float32 values.

    Returns:
        NumPy array of same shape with each row having L2 norm == 1.0
        (except zero vectors, which remain zero).

    Raises:
        ValueError: If input is not a 2D array.
    """
    if vectors.ndim != 2:
        raise ValueError(
            f"Expected 2D array, got {vectors.ndim}D array with shape {vectors.shape}"
        )

    norms = np.linalg.norm(vectors, axis=1, keepdims=True)

    # Avoid division by zero for zero-norm vectors.
    safe_norms = np.where(norms == 0, 1.0, norms)
    normalized = vectors / safe_norms

    # Ensure float32 output.
    normalized = normalized.astype(np.float32)

    logger.debug(
        "Normalized %d vectors. Min norm: %.6f, Max norm: %.6f",
        vectors.shape[0],
        float(np.min(norms)),
        float(np.max(norms)),
    )
    return normalized


def validate_embeddings(
    vectors: np.ndarray,
    *,
    dimension: int = DEFAULT_SETTINGS.vector_dimension,
    tolerance: float = DEFAULT_SETTINGS.norm_tolerance,
) -> bool:
    """Validate that embeddings meet dimensional and normalization requirements.

    Checks:
    1. Shape is (N, dimension) where dimension defaults to 384.
    2. Data type is float32.
    3. Every row vector has L2 norm within tolerance of 1.0.

    Args:
        vectors: NumPy array to validate.
        dimension: Expected embedding dimensionality (default: 384).
        tolerance: Allowed deviation from unit norm (default: 1e-5).

    Returns:
        True if all validations pass.

    Raises:
        ValueError: If any validation check fails, with a descriptive message.
    """
    # Check dimensionality.
    if vectors.ndim != 2:
        raise ValueError(
            f"Expected 2D array, got {vectors.ndim}D with shape {vectors.shape}"
        )

    if vectors.shape[1] != dimension:
        raise ValueError(
            f"Expected dimension {dimension}, got {vectors.shape[1]}. "
            f"Shape: {vectors.shape}"
        )

    # Check dtype.
    if vectors.dtype != np.float32:
        raise ValueError(
            f"Expected float32, got {vectors.dtype}"
        )

    # Check L2 norms.
    norms = np.linalg.norm(vectors, axis=1)
    non_unit = np.abs(norms - 1.0) > tolerance
    non_unit_count = int(np.sum(non_unit))

    if non_unit_count > 0:
        worst_idx = int(np.argmax(np.abs(norms - 1.0)))
        worst_norm = float(norms[worst_idx])
        raise ValueError(
            f"{non_unit_count} vectors are not L2-normalized (tolerance={tolerance}). "
            f"Worst: index={worst_idx}, norm={worst_norm:.8f}"
        )

    logger.info(
        "Validation passed: %d vectors, dimension=%d, all L2-normalized.",
        vectors.shape[0],
        dimension,
    )
    return True
