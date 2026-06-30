# Storage & Retrieval Module Architecture

## Overview

The Storage & Retrieval module is responsible for storing, retrieving, and ranking candidate resumes using **Qdrant Vector Database** and **FastEmbed** embeddings.

It supports three search modes:

- **Vector Search** – Semantic similarity search using embeddings
- **Keyword Search** – Exact keyword matching using indexed payload fields  
- **Hybrid Search** – Combines semantic and keyword search with configurable weighted ranking

## Architecture Flow

```
Resume
    │
    ▼
FastEmbed Embedding
    │
    ▼
Qdrant Vector Database
    │
    ├───────────────► Vector Search
    │
    ├───────────────► Keyword Search
    │
    ▼
Merge Results
    │
Normalize Scores
    │
Weighted Ranking
    │
    ▼
Top-K Candidates
```

## Hybrid Search Pipeline

```
Query
    │
    ├────────► Vector Search
    │
    ├────────► Keyword Search
    │
Merge Results
    │
Normalize Scores
    │
Weighted Ranking
    │
Return Top-K
```

## Ranking Formula

```
Final Score =
(Vector Score × VECTOR_WEIGHT)
+
(Keyword Score × KEYWORD_WEIGHT)
```

Default configuration:
- VECTOR_WEIGHT = 0.7
- KEYWORD_WEIGHT = 0.3

Weights can be changed in `services/storage/config.py`

## Configuration

Required environment variables:

- `QDRANT_HOST`
- `QDRANT_PORT`
- `QDRANT_COLLECTION_NAME`
- `EMBEDDING_MODEL_NAME`
- `VECTOR_WEIGHT`
- `KEYWORD_WEIGHT`
- `OVERFETCH_FACTOR`

## Setup

Start Qdrant using Docker:

```bash
docker run -p 6333:6333 qdrant/qdrant
```

Initialize the collection:

```python
from services.storage.qdrant_setup import setup_qdrant

setup_qdrant()
```