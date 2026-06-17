"""Batch embedding generation using FastEmbed.

Uses BAAI/bge-small-en-v1.5 via the FastEmbed ONNX runtime for
efficient inference. Supports device awareness for GPU logging,
though FastEmbed uses ONNX Runtime under the hood.

For actual GPU acceleration, install ``onnxruntime-gpu`` to enable
the CUDAExecutionProvider automatically.
"""

import logging
from collections.abc import Iterator

import numpy as np
from fastembed import TextEmbedding

from resume_embedding.config.settings import DEFAULT_SETTINGS

logger = logging.getLogger(__name__)

# Module-level model cache to avoid re-loading the model on every call.
_model_cache: dict[str, TextEmbedding] = {}


def _get_model(model_name: str) -> TextEmbedding:
    """Get or create a cached TextEmbedding model instance.

    Args:
        model_name: HuggingFace model identifier.

    Returns:
        A TextEmbedding instance ready for inference.
    """
    if model_name not in _model_cache:
        logger.info("Loading embedding model: %s", model_name)
        _model_cache[model_name] = TextEmbedding(model_name=model_name)
        logger.info("Model loaded successfully: %s", model_name)
    return _model_cache[model_name]


def generate_embeddings(
    texts: list[str],
    *,
    model_name: str = DEFAULT_SETTINGS.model_name,
    batch_size: int = DEFAULT_SETTINGS.default_batch_size,
    device: str = "cpu",
) -> np.ndarray:
    """Generate dense vector embeddings for a batch of texts.

    Uses FastEmbed's ONNX-based inference. The model is cached after first load.
    The ``device`` parameter is logged for metadata tracking; FastEmbed
    automatically uses CUDAExecutionProvider when ``onnxruntime-gpu`` is installed.

    Args:
        texts: List of text strings to embed.
        model_name: HuggingFace model identifier.
        batch_size: Number of texts to process per inference batch.
        device: Compute device indicator ('cuda' or 'cpu'). Used for logging
            and metadata. FastEmbed handles provider selection internally.

    Returns:
        NumPy array of shape (len(texts), 384) with float32 embeddings.

    Raises:
        ValueError: If texts is empty.
    """
    if not texts:
        raise ValueError("Cannot generate embeddings for an empty text list.")

    model = _get_model(model_name)

    logger.debug("Generating embeddings for %d texts on device=%s", len(texts), device)

    embeddings_iter: Iterator[np.ndarray] = model.embed(
        texts,
        batch_size=batch_size,
    )

    embeddings_list = list(embeddings_iter)
    result = np.array(embeddings_list, dtype=np.float32)

    logger.debug(
        "Generated embeddings: shape=%s, dtype=%s",
        result.shape,
        result.dtype,
    )
    return result
