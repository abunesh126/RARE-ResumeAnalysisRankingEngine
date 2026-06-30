# Resume Embedding Engine — Command Reference

## Setup

```bash
cd /workspaces/RARE-ResumeAnalysisRankingEngine/resume_embedding

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
pip install onnxruntime-gpu>=1.17.0    # optional, GPU support
```

---
## Embedding Pipeline

```bash
# Sample data (10 bundled records)
python scripts/run_sample.py

# JSONL input
python -m resume_embedding.main --input data/input/candidates.jsonl

# JSON array input
python -m resume_embedding.main --input data/input/sample_candidates.json

# Force CPU
python -m resume_embedding.main --input data.jsonl --device cpu

# Force GPU
python -m resume_embedding.main --input data.jsonl --device cuda

# Custom output directory
python -m resume_embedding.main --input data.jsonl --output data/output/my_run

# Custom config
python -m resume_embedding.main --input data.jsonl --config configs/model.yaml

# Resume interrupted run
python -m resume_embedding.main --resume --output data/output/run_20260617_091508

# Custom batch size
python -m resume_embedding.main --input data.jsonl --batch-size 512
```

---
## Viewer (inspect .npy output)

```bash
# Summary + top similar pairs
python viewer/view_embeddings.py data/output/run_<timestamp>

# Show one candidate's vector details
python viewer/view_embeddings.py data/output/run_<timestamp> --show CAND_0000001

# Find 5 most similar candidates
python viewer/view_embeddings.py data/output/run_<timestamp> --similar CAND_0000001 --top 5

# Top 10 most similar pairs in the dataset
python viewer/view_embeddings.py data/output/run_<timestamp> --pairs --top 10

# Compare two specific candidates
python viewer/view_embeddings.py data/output/run_<timestamp> --compare CAND_0000025 CAND_0000044
```

---
## Tests

```bash
# Run all 182 tests (inside venv)
python -m pytest tests/ -v

# Run specific test files
python -m pytest tests/test_candidate_parser.py -v
python -m pytest tests/test_text_builder.py -v
python -m pytest tests/test_pipeline_integration.py -v

# Run with short traceback
python -m pytest tests/ -v --tb=short
```

---
## Benchmarking

```bash
python scripts/benchmark.py --num-candidates 1000 --device cpu
python scripts/benchmark.py --num-candidates 1000 --device cuda
```

---
## Linting

```bash
ruff check resume_embedding/ tests/
ruff format resume_embedding/ tests/
```