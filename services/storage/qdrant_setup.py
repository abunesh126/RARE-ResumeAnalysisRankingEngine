"""
Setup script for Qdrant vector database.

Creates the collection (if it does not already exist),
initializes the vector size using the configured embedding model,
and creates payload indexes required for Hybrid Search.
"""

import logging

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import (
    Distance,
    VectorParams,
    PayloadSchemaType,
)

from services.storage.config import (
    EMBEDDING_MODEL_NAME,
    QDRANT_COLLECTION_NAME,
    QDRANT_HOST,
    QDRANT_PORT,
)

logger = logging.getLogger(__name__)


def setup_qdrant(
    collection_name: str = QDRANT_COLLECTION_NAME,
    host: str = QDRANT_HOST,
    port: int = QDRANT_PORT,
) -> QdrantClient:
    """
    Initialize the Qdrant collection.

    This function:

    1. Connects to Qdrant.
    2. Creates the collection if it does not exist.
    3. Determines embedding dimension automatically.
    4. Creates payload indexes for Hybrid Search.
    5. Returns the initialized client.
    """

    logger.info("Connecting to Qdrant at %s:%s", host, port)

    client = QdrantClient(host=host, port=port)

    embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL_NAME)

    # -------------------------------------------------------------
    # Check whether the collection already exists
    # -------------------------------------------------------------
    try:
        client.get_collection(collection_name=collection_name)
        collection_exists = True
        logger.info("Collection '%s' already exists.", collection_name)

    except UnexpectedResponse:
        collection_exists = False
        logger.info("Collection '%s' does not exist.", collection_name)

    # -------------------------------------------------------------
    # Create collection if required
    # -------------------------------------------------------------
    if not collection_exists:

        logger.info("Determining embedding dimension...")

        sample_embedding = list(embedding_model.embed(["test"]))[0]

        embedding_dimension = len(sample_embedding)

        logger.info(
            "Embedding dimension detected: %s",
            embedding_dimension,
        )

        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=embedding_dimension,
                distance=Distance.COSINE,
            ),
        )

        logger.info(
            "Created Qdrant collection '%s'.",
            collection_name,
        )

    # -------------------------------------------------------------
    # Create payload indexes for Hybrid Search
    # -------------------------------------------------------------

    payload_indexes = [
        ("resume_text", PayloadSchemaType.TEXT),
        ("skills", PayloadSchemaType.KEYWORD),
    ]
    for field_name, field_type in payload_indexes:

        try:

            client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_type=field_type,
            )

            logger.info(
                "Created payload index on '%s'.",
                field_name,
            )

        except Exception:

            logger.debug(
                "Payload index '%s' already exists or could not be created.",
                field_name,
            )

    logger.info("Qdrant setup completed successfully.")

    return client


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    setup_qdrant()