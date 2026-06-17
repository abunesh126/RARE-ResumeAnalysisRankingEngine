# Resume Embedding Engine

> Converts candidate JSON/JSONL profiles → 384-dimensional dense vectors, ready for search, ranking, or matching systems.

---

## What This Does (and Doesn't Do)

| ✅ This pipeline does | ❌ This pipeline does NOT |
|---|---|
| Parse & validate candidate JSON/JSONL | Rank or score candidates |
| Build semantic text from profiles | Search or query embeddings |
| Generate 384-D BGE-Small embeddings | Build FAISS / Milvus indexes |
| L2-normalize vectors (cosine-ready) | Match jobs to resumes |
| Save `.npy` arrays + metadata | Train or fine-tune models |
| GPU acceleration (CUDA / ONNX) | Serve embeddings via API |
| Checkpoint & resume long jobs | |

**Bottom line:** This is an upstream component. Feed it a `.jsonl` or `.json` file, get back vectors. A downstream system does the matching.

---

## 5-Minute Setup

```bash
cd resume_embedding
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
pip install -e .

# Optional: GPU support
pip install onnxruntime-gpu>=1.17.0
```

### Run on sample data (10 records, no setup needed)

```bash
python scripts/run_sample.py
```

### Run on your data

```bash
# JSONL (100k records, streamed line-by-line)
python -m resume_embedding.main --input datasets/input/candidates.jsonl

# JSON array (loaded into memory)
python -m resume_embedding.main --input path/to/sample_candidates.json
```

Output lands in `outputs/run_YYYYMMDD_HHMMSS/` automatically.

---

## Architecture

```
Candidate JSON / JSONL
      │
      ▼
Schema Validation          ← Pydantic — rejects bad records early
      │
      ▼
Text Builder               ← Converts JSON → section-ordered text
      │
      ▼
BGE-Small-v1.5 (ONNX)     ← FastEmbed inference, GPU or CPU
      │
      ▼
L2 Normalization           ← Unit-norm → use np.dot() for cosine similarity
      │
      ▼
NumPy Storage
   ├── embeddings.npy       shape (N, 384), float32
   ├── candidate_ids.npy    shape (N,),     aligned 1:1 with embeddings
   └── metadata.json        model, device, timestamp, record count
```

---

## Pipeline Modules

Each module has one job. Here's what lives where:

| Module | File | What it does |
|---|---|---|
| Parser | `parser/candidate_parser.py` | Reads `.jsonl` or `.json`, validates each record against Pydantic schema |
| Text Builder | `formatter/text_builder.py` | Converts `CandidateProfile` → structured text string |
| Embedder | `embedding/embedder.py` | Runs FastEmbed inference, returns raw vectors |
| Normalizer | `embedding/normalizer.py` | L2-normalizes + validates shape and norm |
| Storage | `storage/npy_writer.py` | Saves `embeddings.npy` and `candidate_ids.npy` |
| Metadata | `storage/metadata_writer.py` | Writes `metadata.json` for traceability |
| Checkpoint | `pipeline/checkpoint.py` | Saves progress every N records; enables `--resume` |
| Orchestrator | `pipeline/embedding_pipeline.py` | Wires everything together, drives the batch loop |
| Config | `config/settings.py` | Loads YAML, detects GPU |

---

## Text Builder — Where Embedding Quality Comes From

Raw JSON isn't useful to an embedding model. The text builder converts each candidate record into a structured string, ordered by **semantic density** — the most discriminating fields come first so the model weights them higher.

### Section Order

```
[CURRENT_TITLE]     ← strongest signal (job role)
[HEADLINE]          ← professional identity
[SUMMARY]           ← self-described expertise
[SKILLS]            ← technical competencies
[EXPERIENCE]        ← work history + descriptions
[EDUCATION]         ← academic background
[CERTIFICATIONS]    ← credentials
[LANGUAGES]         ← proficiencies
[METADATA]          ← location, industry, company
```

### Example: JSON → Embedding Text

**Input (abbreviated):**
```json
{
  "current_title": "Backend Engineer",
  "headline": "Backend Engineer | SQL, Spark, Cloud",
  "summary": "Software / data professional with 6.9 years..."
}
```

**Output text fed to the model:**
```
[CURRENT_TITLE]
Backend Engineer

[HEADLINE]
Backend Engineer | SQL, Spark, Cloud

[SUMMARY]
Software / data professional with 6.9 years of experience building data pipelines...

[SKILLS]
Tailwind (intermediate) | NLP (advanced) | Image Classification (advanced)

[EXPERIENCE]
Backend Engineer at Mindtree (IT Services, 10001+) - 27 months
Implemented streaming data pipelines on Kafka and Spark Streaming...

[EDUCATION]
B.E. in Computer Science from Lovely Professional University (2017–2020) - 8.24 CGPA

[LANGUAGES]
English (professional) | Hindi (conversational)

[METADATA]
Location: Toronto, Canada | Industry: IT Services | Experience: 6.9 years
```

> **Why `redrob_signals` is excluded:** Platform behavioral metrics (profile views, recruiter response rate, salary range) are numeric/behavioral — not semantic. Including them adds noise to the text embedding and hurts retrieval quality.

---

## Output Files

Every run creates a timestamped directory. Nothing is ever overwritten.

```
outputs/
├── run_20260617_091508/
│   ├── embeddings.npy       ← (N, 384) float32 — the vectors
│   ├── candidate_ids.npy    ← (N,) str — "CAND_0000001", aligned to embeddings
│   ├── metadata.json        ← run provenance
│   ├── logs/
│   └── checkpoints/         ← cleared on successful completion
```

### Reading the output

```python
import numpy as np

embeddings   = np.load("outputs/run_.../embeddings.npy")
candidate_ids = np.load("outputs/run_.../candidate_ids.npy", allow_pickle=True)

# Cosine similarity (vectors are already L2-normalized)
score = np.dot(embeddings[0], embeddings[1])
```

### `metadata.json` example

```json
{
  "model": "BAAI/bge-small-en-v1.5",
  "dimension": 384,
  "normalized": true,
  "device": "cuda",
  "records_processed": 100000,
  "input_file": "datasets/input/candidates.jsonl",
  "timestamp": "2026-06-17T03:30:00+00:00"
}
```

---

## Common Commands

```bash
# Quick test (10 sample records)
python scripts/run_sample.py

# Full dataset (.jsonl), auto device
python -m resume_embedding.main --input datasets/input/candidates.jsonl

# JSON array input (.json)
python -m resume_embedding.main --input path/to/sample_candidates.json

# Force GPU
python -m resume_embedding.main --input data.jsonl --device cuda

# Force CPU
python -m resume_embedding.main --input data.jsonl --device cpu

# Custom output directory
python -m resume_embedding.main --input data.jsonl --output outputs/my_run/

# Resume an interrupted run
python -m resume_embedding.main --resume --output outputs/run_20260617_091508/

# Custom config
python -m resume_embedding.main --input data.jsonl --config configs/model.yaml

# Benchmark your hardware
python scripts/benchmark.py --num-candidates 1000 --device cuda
```

---

## Python API

```python
# Simple usage
from resume_embedding import run_pipeline

result = run_pipeline(input_path="data.jsonl")  # also accepts .json
print(result["total_candidates"])   # 100000
print(result["embeddings_shape"])   # (100000, 384)
print(result["output_dir"])         # outputs/run_20260617_091508

# Advanced usage
from resume_embedding import run_pipeline, PipelineSettings

settings = PipelineSettings.from_yaml("configs/model.yaml")
result = run_pipeline(
    input_path="data.jsonl",
    output_path="./outputs/custom_run",
    batch_size=512,
    device="cuda",
    settings=settings,
)
```

---

## Dataset Format

The pipeline accepts two formats (auto-detected by file extension):

| Extension | Format | Memory | Best for |
|---|---|---|---|
| `.jsonl` | One JSON object per line | Streaming (low memory) | Large datasets (100k+) |
| `.json` | JSON array of objects | Loaded into memory | Small datasets, samples |

Each record must follow this schema:

```json
{
  "candidate_id": "CAND_0000001",
  "profile": {
    "anonymized_name": "Ira Vora",
    "headline": "Backend Engineer | SQL, Spark, Cloud",
    "summary": "Software / data professional with 6.9 years ...",
    "location": "Toronto",
    "country": "Canada",
    "years_of_experience": 6.9,
    "current_title": "Backend Engineer",
    "current_company": "Mindtree",
    "current_company_size": "10001+",
    "current_industry": "IT Services"
  },
  "career_history": [
    {
      "company": "Mindtree",
      "title": "Backend Engineer",
      "start_date": "2024-03-08",
      "end_date": null,
      "duration_months": 27,
      "is_current": true,
      "industry": "IT Services",
      "company_size": "10001+",
      "description": "Implemented streaming data pipelines..."
    }
  ],
  "education": [
    {
      "institution": "Lovely Professional University",
      "degree": "B.E.",
      "field_of_study": "Computer Science",
      "start_year": 2017,
      "end_year": 2020,
      "grade": "8.24 CGPA",
      "tier": "tier_3"
    }
  ],
  "skills": [
    { "name": "NLP", "proficiency": "advanced", "endorsements": 37, "duration_months": 26 }
  ],
  "certifications": [
    { "name": "AWS Certified Cloud Practitioner", "issuer": "AWS", "year": 2025 }
  ],
  "languages": [
    { "language": "English", "proficiency": "professional" }
  ],
  "redrob_signals": { "...": "excluded from embedding" }
}
```

### Which fields are used?

| Field | Used in embedding? |
|---|:---:|
| `profile` (title, headline, summary, location, industry) | ✅ |
| `skills` | ✅ |
| `education` | ✅ |
| `career_history` | ✅ |
| `certifications` | ✅ |
| `languages` | ✅ |
| `redrob_signals` (behavioral metrics) | ❌ |
| `candidate_id` | Used as identifier only |

---

## Configuration

Default settings (`configs/default.yaml`):

```yaml
model_name: "BAAI/bge-small-en-v1.5"
vector_dimension: 384
default_batch_size: 256
device: "auto"            # auto | cuda | cpu
checkpoint_interval: 1000
norm_tolerance: 1.0e-5
```

Override with `--config path/to/custom.yaml` or individual CLI flags.

### GPU Auto-Detection (`device: auto`)

The pipeline checks in order:
1. `torch.cuda.is_available()` (if PyTorch is installed)
2. `onnxruntime.get_available_providers()` for `CUDAExecutionProvider`
3. Falls back to CPU

---

## Checkpointing

The pipeline saves a checkpoint every `checkpoint_interval` records (default: 1000).

```
Batch 1: records    0–999   → checkpoint saved
Batch 2: records 1000–1999  → checkpoint saved
...
```

If the job is interrupted for any reason:

```bash
python -m resume_embedding.main --resume --output outputs/run_20260617_091508/
```

It reads `checkpoints/checkpoint_state.json`, loads all completed batches, and continues from the next unprocessed record. Checkpoint files are deleted automatically on successful completion.

---

## Why BGE-Small-v1.5?

| Model | Dimensions | Why not? |
|---|---|---|
| MiniLM-L6 | 384 | Lower MTEB retrieval accuracy |
| E5-small | 384 | Requires `query:` / `passage:` prefixes — extra complexity |
| GTE-small | 384 | Fewer benchmarks, smaller community |
| **BGE-Small-v1.5** | **384** | **Best retrieval quality in class, no prefix formatting, native ONNX** |
| BGE-Base | 768 | 2× memory and compute — overkill for this use case |

BGE-Small-v1.5 ranks top-tier on MTEB retrieval benchmarks at the 384-dimension level, requires no special input formatting, and runs natively on ONNX Runtime with GPU acceleration.

---

## Performance

| Dataset Size | Device | Estimated Time |
|---|---|---|
| 10 | CPU | < 1 second |
| 100 | CPU | Seconds |
| 1,000 | CPU | < 1 minute |
| 10,000 | CPU | A few minutes |
| 100,000 | GPU (RTX 5070 Ti) | Significantly faster than CPU |
| 100,000 | CPU | Extended — use GPU for large datasets |

Benchmark your specific hardware:
```bash
python scripts/benchmark.py --num-candidates 1000 --device cuda
```

---

## Tests

```bash
pytest tests/ -v
```

95 tests covering: parser (JSONL + JSON array), text builder, embedder, normalizer, storage, checkpoints, YAML config, device detection, and full pipeline integration.

---

## Project Structure

```
resume_embedding/
├── configs/
│   ├── default.yaml                     # Default pipeline settings
│   └── model.yaml                       # Model-specific overrides
│
├── datasets/
│   ├── sample/sample_candidates.jsonl   # 10 bundled test records
│   └── input/.gitkeep                   # Drop your .jsonl or .json here
│
├── scripts/
│   ├── run_sample.py                    # Quick test on sample data
│   ├── run_dataset.py                   # Full dataset processing
│   └── benchmark.py                     # Throughput benchmarking
│
├── src/resume_embedding/
│   ├── config/settings.py               # YAML config + GPU detection
│   ├── parser/candidate_parser.py       # Pydantic schema validation
│   ├── formatter/text_builder.py        # Structured text builder
│   ├── embedding/embedder.py            # FastEmbed inference
│   ├── embedding/normalizer.py          # L2 normalization + validation
│   ├── pipeline/embedding_pipeline.py   # Orchestration + batch loop
│   ├── pipeline/checkpoint.py           # Crash recovery
│   ├── storage/npy_writer.py            # NumPy persistence
│   └── storage/metadata_writer.py       # Run metadata
│
├── tests/                               # 95 unit + integration tests
├── outputs/                             # Generated vectors (gitignored)
├── pyproject.toml
└── requirements.txt
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `fastembed` | ONNX embedding inference |
| `numpy` | Array storage and normalization |
| `orjson` | Fast JSON parsing |
| `pydantic` | Schema validation |
| `pyyaml` | YAML config loading |
| `tqdm` | Progress bars |
| `onnxruntime-gpu` *(optional)* | CUDA acceleration |
| `torch` *(optional)* | GPU auto-detection |

---

## Roadmap

```
[ ] Multi-language embedding support
[ ] Multiple model selection (BGE-Base, GTE, E5)
[ ] Quantized embeddings (int8) for reduced storage
[ ] Multi-GPU / distributed processing
[ ] Docker container
[ ] Hugging Face Hub export
[ ] Optional FAISS index generation
[ ] Streaming API for real-time embedding
```

---

## License

MIT
