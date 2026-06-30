# Storage & Retrieval Module

Vector database storage and hybrid search for candidate resumes using **Qdrant** and **FastEmbed**.

## Features

- Resume ingestion with metadata storage
- Vector similarity search (semantic matching)
- Keyword search (exact term matching)
- Hybrid search (70% vector + 30% keyword weighted ranking)
- Candidate deduplication
- Score normalization

## Setup

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Start Qdrant

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### Initialize Collection

```python
from services.storage.qdrant_setup import setup_qdrant

setup_qdrant()
```

## Usage

### Ingest a Candidate

```python
from services.storage.retrieval import ResumeRetriever

retriever = ResumeRetriever()

retriever.ingest_candidate({
    "candidate_id": 1,
    "name": "Alice",
    "resume_text": "Python developer with AWS experience",
    "skills": ["Python", "AWS"],
    "experience": 5
})
```

### Search Candidates

```python
# Vector search
results = retriever.search("Python Backend Engineer", search_type="vector", top_k=5)

# Keyword search
results = retriever.search("Python AWS", search_type="keyword", top_k=5)

# Hybrid search
results = retriever.search("Python AWS Developer", search_type="hybrid", top_k=5)
```

### Get Candidate by ID

```python
resume = retriever.get_resume(1)
```

## API Endpoints

When running with Flask:

- `POST /search` - Search candidates (hybrid/vector/keyword)
- `POST /ingest` - Ingest a new candidate
- `GET /resume/<candidate_id>` - Get candidate by ID
- `GET /health` - Health check

## Configuration

Environment variables (via `.env`):

```
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=resumes
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5
VECTOR_WEIGHT=0.7
KEYWORD_WEIGHT=0.3
OVERFETCH_FACTOR=3
```

## Project Structure

```
services/storage/
├── __init__.py         # Public exports
├── config.py           # Configuration constants
├── qdrant_setup.py     # Qdrant collection initialization
├── retrieval.py        # ResumeRetriever class with search methods
├── app.py              # Flask API endpoints
└── sample_resumes.py   # Mock data for testing
```