# Resume Embedding Engine

> Converts resume files in multiple formats (JSONL, JSON, PDF, Markdown, Plain Text, PNG/JPG/JPEG/BMP/TIFF) into 384-dimensional L2-normalized dense vectors, ready for search, ranking, or candidate matching systems.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Repository Structure](#repository-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Input Formats](#input-formats)
- [Running the Project](#running-the-project)
- [Sample Execution](#sample-execution)
- [Output Files](#output-files)
- [Pipeline Explanation](#pipeline-explanation)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Performance Notes](#performance-notes)
- [Development Guide](#development-guide)
- [License](#license)

---

## Project Overview

### Purpose

The Resume Embedding Engine is an **upstream preprocessing component** for candidate search and ranking systems. It accepts resumes in any supported format and outputs dense float32 vectors that can be plugged directly into a FAISS index, a Milvus collection, a vector database, or a custom cosine similarity search.

### Key Features

| Feature | Detail |
|---|---|
| **Multi-format input** | JSONL, JSON, PDF, Markdown, Plain Text, PNG, JPG, BMP, TIFF |
| **Unified output** | Always 384-dimensional L2-normalized float32 vectors |
| **Format-agnostic pipeline** | The embedding stage never sees the file format |
| **GPU acceleration** | CUDA via `onnxruntime-gpu`, auto-detected |
| **Crash recovery** | Checkpoint-and-resume for large datasets |
| **Streaming** | JSONL files are streamed line-by-line — no full load into memory |
| **Schema validation** | Pydantic V2 validates every structured record |
| **Production-grade** | Typed, documented, fully tested (182 tests) |

### What This Engine Does NOT Do

| ❌ Not included |
|---|
| Rank or score candidates |
| Search or query embeddings |
| Build FAISS / Milvus / Qdrant indexes |
| Match jobs to resumes |
| Train or fine-tune models |
| Serve embeddings via API |

This is an upstream component. Feed it resumes, get back vectors.

### Embedding Model

| Property | Value |
|---|---|
| Model | `BAAI/bge-small-en-v1.5` |
| Runtime | FastEmbed (ONNX) |
| Dimension | 384 |
| Type | `float32` |
| Normalization | L2 (unit norm — use `np.dot()` for cosine similarity) |

BGE-Small-v1.5 ranks top-tier on MTEB retrieval benchmarks at the 384-dimension level, requires no special input formatting (`query:` / `passage:` prefixes), and runs natively on ONNX Runtime with optional GPU acceleration.

---

## Repository Structure

```
resume_embedding/
│
├── resume_embedding/                # Python package (installable)
│   ├── __init__.py                  # Public API: run_pipeline, dispatch, PipelineSettings, etc.
│   ├── main.py                      # Thin shim — re-exports the CLI entry point
│   └── app/
│       ├── __init__.py
│       ├── config.py                # PipelineSettings (Pydantic) + YAML loading + GPU detection
│       ├── io.py                    # Pydantic schemas, JSONL/JSON loader, NPY writer, metadata, CheckpointManager
│       ├── input.py                 # Format dispatcher + all readers + resume text normalizer
│       ├── model.py                 # Candidate text builder + FastEmbed inference + L2 normalization
│       ├── pipeline.py              # run_pipeline() orchestrator — drives the full end-to-end flow
│       └── main.py                  # CLI entry point (argparse)
│
├── configs/
│   ├── default.yaml                 # Default pipeline settings (model, batch size, device, etc.)
│   └── model.yaml                   # Model-specific override example
│
├── data/
│   ├── input/                       # Drop your input files here (.jsonl / .json / .pdf / etc.)
│   ├── output/                      # Generated run directories land here (gitignored)
│   └── sample/
│       └── sample_candidates.jsonl  # 10 bundled sample records for quick testing
│
├── scripts/
│   ├── run_sample.py                # One-command sample test (wraps run_pipeline)
│   ├── run_dataset.py               # Full dataset wrapper (delegates to the CLI)
│   └── benchmark.py                 # Throughput benchmark for hardware profiling
│
├── tests/                           # 182 unit + integration tests (pytest)
│   ├── conftest.py                  # Shared fixtures (sample candidates, embeddings, tmp paths)
│   ├── test_candidate_parser.py     # Pydantic schema + JSONL/JSON loading
│   ├── test_checkpoint.py           # CheckpointManager save/load/clear
│   ├── test_config_yaml.py          # YAML loading, device detection, overrides
│   ├── test_embedder.py             # FastEmbed inference (mocked)
│   ├── test_image_reader.py         # OCR reader (mocked pytesseract + Pillow)
│   ├── test_input_dispatcher.py     # dispatch() + detect_input_type() routing
│   ├── test_markdown_reader.py      # Markdown stripping + loading
│   ├── test_metadata_writer.py      # metadata.json writing
│   ├── test_normalizer.py           # l2_normalize + validate_embeddings
│   ├── test_npy_writer.py           # save_embeddings + load_embeddings
│   ├── test_pdf_reader.py           # PDF reader (mocked fitz)
│   ├── test_pipeline_integration.py # End-to-end pipeline (mocked embedding model)
│   ├── test_resume_normalizer.py    # normalize_resume_text()
│   ├── test_text_builder.py         # candidate_to_text() section builder
│   ├── test_text_reader.py          # Plain text reader
│   └── test_validation.py           # Shape, dtype, and norm validation
│
├── viewer/
│   └── view_embeddings.py           # CLI tool to inspect, search, and compare .npy outputs
│
├── .github/
│   ├── workflows/ci.yml             # GitHub Actions CI (lint + test on Python 3.11/3.12)
│   ├── ISSUE_TEMPLATE/              # Bug report and feature request templates
│   └── pull_request_template.md     # PR template
│
├── pyproject.toml                   # Build config, dependencies, optional extras, ruff/pytest settings
├── requirements.txt                 # Pinned dependencies for reproducible installs
├── README.md                        # This file
├── LICENSE                          # MIT
├── .editorconfig                    # Editor formatting rules
└── .gitignore                       # Git ignore rules
```

### Module Responsibilities

| Module | Responsibility |
|---|---|
| `config.py` | Immutable `PipelineSettings` dataclass. Loads YAML, applies CLI overrides, auto-detects GPU via torch/onnxruntime. |
| `io.py` | All I/O: Pydantic schemas (`CandidateProfile`, `ProfileInfo`, etc.), JSONL/JSON streaming loader, `.npy` writer/loader, `metadata.json` writer, `CheckpointManager`. |
| `input.py` | Format dispatcher (`dispatch`, `detect_input_type`), all format-specific readers (JSON, JSONL, PDF, Image, Markdown, Text), and `normalize_resume_text()` for unstructured text. |
| `model.py` | `candidate_to_text()` text builder, `generate_embeddings()` FastEmbed inference, `l2_normalize()`, `validate_embeddings()`. |
| `pipeline.py` | `run_pipeline()` — the single orchestrator that wires all modules together: dispatch → text → embed → normalize → checkpoint → save → metadata. |
| `main.py` (app/) | `argparse` CLI, logging setup, settings construction, error handling. |

---

## Requirements

### Python

- **Python 3.11 or 3.12** (required)

### Operating System

- Windows 10/11
- Ubuntu 20.04+
- macOS 12+

### Core Dependencies (always required)

| Package | Purpose |
|---|---|
| `fastembed >= 0.4.0` | ONNX embedding inference |
| `numpy >= 1.26.0` | Array storage and normalization |
| `orjson >= 3.10.0` | Fast JSON parsing |
| `pydantic >= 2.7.0` | Schema validation |
| `pyyaml >= 6.0` | YAML config loading |
| `tqdm >= 4.66.0` | Progress bars |

### Optional Dependencies

| Feature | Package(s) | Install command |
|---|---|---|
| GPU acceleration | `onnxruntime-gpu >= 1.17.0` | `pip install "resume-embedding[gpu]"` |
| PDF support | `pymupdf >= 1.24.0` | `pip install "resume-embedding[pdf]"` |
| Image OCR | `pytesseract >= 0.3.10`, `Pillow >= 10.0.0` | `pip install "resume-embedding[ocr]"` |
| All formats | all of the above | `pip install "resume-embedding[all-formats]"` |

#### Tesseract Binary (required for Image OCR)

The `pytesseract` Python package is just a wrapper — Tesseract itself must be installed separately:

| OS | Command |
|---|---|
| Windows | [Download installer](https://github.com/UB-Mannheim/tesseract/wiki) — add to PATH |
| Ubuntu | `sudo apt install tesseract-ocr` |
| macOS | `brew install tesseract` |

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/RARE-ResumeAnalysisRankingEngine.git
cd RARE-ResumeAnalysisRankingEngine/services/resume_embedding
```

### 2. Create and Activate a Virtual Environment

#### Windows — Command Prompt

```cmd
python -m venv .venv
.venv\Scripts\activate
```

#### Windows — PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

> If you see a policy error in PowerShell, run:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

#### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

### 4. (Optional) Install Format Extras

```bash
# GPU acceleration
pip install "resume-embedding[gpu]"

# PDF support
pip install "resume-embedding[pdf]"

# Image OCR support (also install the Tesseract binary — see Requirements)
pip install "resume-embedding[ocr]"

# All optional formats at once
pip install "resume-embedding[all-formats]"
```

---

## Configuration

### Default Configuration (`configs/default.yaml`)

```yaml
model_name: "BAAI/bge-small-en-v1.5"
vector_dimension: 384
default_batch_size: 256
device: "auto"            # auto | cuda | cpu
checkpoint_interval: 1000
norm_tolerance: 1.0e-5
```

### GPU Auto-Detection (`device: auto`)

When `device` is set to `auto`, the pipeline checks in order:
1. `torch.cuda.is_available()` (if PyTorch is installed)
2. `onnxruntime.get_available_providers()` for `CUDAExecutionProvider`
3. Falls back to `cpu`

### Overriding Configuration

**Via YAML file:**
```bash
resume-embed --input data.jsonl --config configs/model.yaml
```

**Via CLI flags (override specific values):**
```bash
resume-embed --input data.jsonl --device cuda --batch-size 512
```

**CLI flags always take priority over YAML values.**

---

## Input Formats

The pipeline auto-detects the format from the file extension.

| Format | Extension(s) | Processing | Optional Package |
|---|---|---|---|
| JSONL | `.jsonl` | Streamed line-by-line, Pydantic-validated | *(core)* |
| JSON | `.json` | Loaded into memory, Pydantic-validated | *(core)* |
| PDF | `.pdf` | Text extraction via PyMuPDF | `pymupdf` |
| Markdown | `.md` | Syntax-stripped to plain text | *(core)* |
| Plain Text | `.txt` | UTF-8 read + whitespace normalization | *(core)* |
| PNG | `.png` | Tesseract OCR (grayscale + sharpen) | `pytesseract`, `Pillow` |
| JPEG | `.jpg`, `.jpeg` | Tesseract OCR | `pytesseract`, `Pillow` |
| BMP | `.bmp` | Tesseract OCR | `pytesseract`, `Pillow` |
| TIFF | `.tiff` | Tesseract OCR | `pytesseract`, `Pillow` |

### Structured Input Schema (JSONL / JSON)

Each record must follow this schema. All fields except `candidate_id` and `profile.anonymized_name` are optional:

```json
{
  "candidate_id": "CAND_0000001",
  "profile": {
    "anonymized_name": "Ira Vora",
    "headline": "Backend Engineer | SQL, Spark, Cloud",
    "summary": "Software professional with 6.9 years of experience...",
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
      "description": "Implemented streaming data pipelines on Kafka..."
    }
  ],
  "education": [...],
  "skills": [
    { "name": "NLP", "proficiency": "advanced", "endorsements": 37, "duration_months": 26 }
  ],
  "certifications": [...],
  "languages": [
    { "language": "English", "proficiency": "professional" }
  ],
  "redrob_signals": { "...": "excluded from embedding — behavioral/numeric metrics only" }
}
```

**Drop your input files into:** `data/input/`

---

## Running the Project

### CLI — All Supported Commands

```bash
# ── Structured input (JSONL / JSON) ───────────────────────────────

# Stream a JSONL dataset (memory-efficient for 100k+ records)
resume-embed --input data/input/candidates.jsonl

# Load a JSON array file
resume-embed --input data/input/candidates.json --device cuda

# ── Unstructured input ────────────────────────────────────────────

# PDF resume (requires PyMuPDF)
resume-embed --input data/input/resume.pdf --output data/output/pdf_run/

# Markdown resume
resume-embed --input data/input/resume.md

# Plain text resume
resume-embed --input data/input/resume.txt

# Image resume — PNG, JPG, BMP, TIFF (requires pytesseract + Pillow + Tesseract binary)
resume-embed --input data/input/resume.png

# ── Device selection ──────────────────────────────────────────────

resume-embed --input data.jsonl --device cuda   # Force GPU
resume-embed --input data.jsonl --device cpu    # Force CPU
resume-embed --input data.jsonl --device auto   # Auto-detect (default)

# ── Advanced options ──────────────────────────────────────────────

# Custom output directory
resume-embed --input data.jsonl --output data/output/my_run/

# Custom batch size
resume-embed --input data.jsonl --batch-size 512

# Custom YAML config
resume-embed --input data.jsonl --config configs/model.yaml

# Enable debug logging
resume-embed --input data.jsonl --verbose

# Resume from last checkpoint
resume-embed --resume --output data/output/run_20260617_091508/

# ── Python module invocation (alternative to the CLI script) ─────

python -m resume_embedding.main --input data.jsonl
python -m resume_embedding.main --input data.jsonl --batch-size 512 --verbose
```

### Python API

```python
# Simple one-liner
from resume_embedding import run_pipeline

result = run_pipeline(input_path="data/sample/sample_candidates.jsonl")
print(result["total_candidates"])    # 10
print(result["embeddings_shape"])    # (10, 384)
print(result["output_dir"])          # data/output/run_20260617_...
print(result["elapsed_seconds"])     # 2.31
print(result["device"])              # "cpu" or "cuda"

# Advanced: custom settings
from resume_embedding import run_pipeline, PipelineSettings

settings = PipelineSettings.from_yaml("configs/model.yaml")
result = run_pipeline(
    input_path="data/input/candidates.jsonl",
    output_path="data/output/custom_run",
    batch_size=512,
    device="cuda",
    settings=settings,
)

# Dispatch any format manually (returns an iterator)
from resume_embedding import dispatch

for candidate_id, text in dispatch("data/input/resume.pdf"):
    print(candidate_id, text[:100])
```

---

## Sample Execution

The bundled sample runs on 10 pre-built records with zero setup:

```bash
python scripts/run_sample.py
```

Expected output:
```
============================================================
SAMPLE RUN — 10 candidates
Input:  .../data/sample/sample_candidates.jsonl
Output: data/output/run_<timestamp>/ (auto-generated)
============================================================

Success: Processed 10 candidates in 3.12s
  Embeddings: (10, 384)
  Device:     cpu
  Output:     data/output/run_20260617_091508
```

---

## Output Files

Every pipeline run creates a **timestamped directory** under `data/output/`. Nothing is ever overwritten.

```
data/output/
└── run_20260617_091508/
    ├── embeddings.npy       ← (N, 384) float32 matrix — the dense vectors
    ├── candidate_ids.npy    ← (N,) string array — IDs aligned 1:1 with embeddings
    ├── metadata.json        ← Run provenance
    └── logs/
        └── run_20260617_091508.log
```

### Reading the Output

```python
import numpy as np

embeddings    = np.load("data/output/run_.../embeddings.npy")
candidate_ids = np.load("data/output/run_.../candidate_ids.npy", allow_pickle=True)

# Cosine similarity (vectors are already L2-normalized — use dot product directly)
score = float(np.dot(embeddings[0], embeddings[1]))
```

### `metadata.json` Example

```json
{
  "model": "BAAI/bge-small-en-v1.5",
  "dimension": 384,
  "normalized": true,
  "device": "cuda",
  "records_processed": 100000,
  "input_file": "data/input/candidates.jsonl",
  "timestamp": "2026-06-17T03:30:00+00:00"
}
```

### Candidate ID Convention

| Input format | Candidate ID |
|---|---|
| `.jsonl` / `.json` | From the record's `candidate_id` field (e.g., `CAND_0000001`) |
| `.pdf`, `.md`, `.txt`, `.png`, `.jpg`, etc. | Derived from filename: `FILE_<stem>` (e.g., `FILE_john_doe_cv`) |

---

## Pipeline Explanation

The pipeline is entirely format-agnostic after the extraction stage.

```
Input File
      │
      ▼
Format Detection (app/input.py: detect_input_type)
      │    auto-detected from file extension
      ▼
Format-Specific Extractor (app/input.py: dispatch)
  ┌───────────────────────────────────────────────────────────────┐
  │  .jsonl / .json  → Pydantic validation → candidate_to_text() │
  │  .pdf            → PyMuPDF page extraction                    │
  │  .png / .jpg / … → Pillow + Tesseract OCR                    │
  │  .md             → Markdown syntax stripping                  │
  │  .txt            → UTF-8 read                                 │
  └───────────────────────────────────────────────────────────────┘
      │  yields (candidate_id, raw_text) tuples
      ▼
Resume Text Normalizer (app/input.py: normalize_resume_text)
      │  removes control chars, collapses whitespace,
      │  strips separator lines, normalizes line endings
      ▼
Text Batching (app/pipeline.py)
      │  collects texts into batches of size `batch_size`
      ▼
Embedding Generation (app/model.py: generate_embeddings)
      │  BAAI/bge-small-en-v1.5 via FastEmbed ONNX
      ▼
L2 Normalization (app/model.py: l2_normalize)
      │  each vector normalized to unit norm
      ▼
Validation (app/model.py: validate_embeddings)
      │  checks shape=(N,384), dtype=float32, all norms≈1.0
      ▼
Checkpoint Save (app/io.py: CheckpointManager)
      │  .npz file per batch, state JSON — enables --resume
      ▼
NumPy Persistence (app/io.py: save_embeddings)
      │  embeddings.npy + candidate_ids.npy
      ▼
Metadata Write (app/io.py: write_metadata)
      │  metadata.json with model, device, timestamp, count
      ▼
Checkpoint Cleanup
      │  checkpoint files deleted on successful completion
      ▼
Result Dictionary returned to caller
```

### Checkpointing & Resume

The pipeline saves a checkpoint every `checkpoint_interval` records (default: 1000).

If the job is interrupted at any point:

```bash
# Resume from where it stopped
resume-embed --resume --output data/output/run_20260617_091508/
```

The checkpoint manager reads `checkpoints/checkpoint_state.json`, reloads completed batch `.npz` files, and continues from the first unprocessed record. Checkpoints are deleted automatically on successful completion.

---

## Testing

### Run All Tests

```bash
# Standard
pytest tests/

# Verbose (shows each test name)
pytest tests/ -v

# Short traceback on failures
pytest tests/ -v --tb=short

# Run a specific test file
pytest tests/test_pipeline_integration.py -v

# Run a specific test class or function
pytest tests/test_input_dispatcher.py::TestDispatch::test_dispatches_jsonl -v
```

### Expected Output

```
============================= 182 passed in 4.38s =============================
```

### Test Coverage by Area

| Area | Test file(s) |
|---|---|
| Pydantic schema + JSONL/JSON loading | `test_candidate_parser.py` |
| Checkpoint save / load / clear | `test_checkpoint.py` |
| YAML config + GPU detection | `test_config_yaml.py` |
| FastEmbed inference | `test_embedder.py` |
| Image OCR reader | `test_image_reader.py` |
| Format dispatch routing | `test_input_dispatcher.py` |
| Markdown stripping + loading | `test_markdown_reader.py` |
| Metadata JSON writing | `test_metadata_writer.py` |
| L2 normalization + validation | `test_normalizer.py` |
| NumPy persistence | `test_npy_writer.py` |
| PDF reader | `test_pdf_reader.py` |
| End-to-end pipeline | `test_pipeline_integration.py` |
| Resume text normalizer | `test_resume_normalizer.py` |
| Text builder sections | `test_text_builder.py` |
| Plain text reader | `test_text_reader.py` |
| Shape/dtype/norm validation | `test_validation.py` |

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'fitz'`
PDF support requires PyMuPDF:
```bash
pip install pymupdf
# or: pip install "resume-embedding[pdf]"
```

### `ModuleNotFoundError: No module named 'pytesseract'` / `ModuleNotFoundError: No module named 'PIL'`
Image OCR requires pytesseract and Pillow:
```bash
pip install pytesseract Pillow
# or: pip install "resume-embedding[ocr]"
```

### `TesseractNotFoundError` — OCR fails with "tesseract is not installed"
The Tesseract binary must be installed separately from the Python package:
- **Windows:** [Download installer](https://github.com/UB-Mannheim/tesseract/wiki), add install directory to PATH
- **Ubuntu:** `sudo apt install tesseract-ocr`
- **macOS:** `brew install tesseract`

### CUDA not detected (`device: auto` falls back to CPU)
- Ensure you have a CUDA-capable GPU and CUDA drivers installed
- Install the GPU runtime: `pip install onnxruntime-gpu`
- Verify CUDA: `python -c "import onnxruntime as ort; print(ort.get_available_providers())"`
- You should see `CUDAExecutionProvider` in the output

### `FileNotFoundError: Input file not found`
Check that the path is correct relative to the directory you are running the command from. Use absolute paths if in doubt:
```bash
resume-embed --input /absolute/path/to/candidates.jsonl
```

### `ValueError: candidate_id must start with 'CAND_'`
All structured records must have a `candidate_id` starting with `CAND_`. Fix your data or use `--skip-invalid` behavior (enabled by default).

### Interrupted run — how to resume
```bash
resume-embed --resume --output data/output/run_20260617_091508/
```
The run directory must exist and contain a `checkpoints/checkpoint_state.json` file.

### `PermissionError` writing outputs
Ensure the `data/output/` directory exists and is writable. On Windows, close any programs that might have the output folder open.

---

## Performance Notes

| Dataset Size | Device | Estimated Time |
|---|---|---|
| 10 records | CPU | < 5 seconds (first run loads model) |
| 100 records | CPU | ~5–10 seconds |
| 1,000 records | CPU | ~30–60 seconds |
| 10,000 records | CPU | A few minutes |
| 100,000 records | GPU (RTX class) | Minutes |
| 100,000 records | CPU | 30–60+ minutes |

### Tuning Tips

- **Increase `batch_size`** for GPUs with large VRAM: `--batch-size 1024`
- **Decrease `batch_size`** if you get OOM errors: `--batch-size 64`
- **Use JSONL** for large datasets — it streams line-by-line with constant memory usage
- **Use `--device cuda`** for any dataset over 10,000 records — the speed difference is significant
- **Model is cached** after first load — subsequent batches are fast

### Benchmarking

```bash
python scripts/benchmark.py --num-candidates 1000 --device cuda
```

---

## Development Guide

### Project Conventions

- **Python 3.11+** — use modern type hints (`list[str]`, `dict[str, int]`, `X | Y`)
- **Pydantic V2** for all schema validation
- **`orjson`** for all JSON parsing (faster than stdlib `json`)
- **No wildcard imports** — all imports are explicit
- **Every public function** has a full docstring with Args, Returns, Raises
- **Linting**: `ruff` — run `ruff check .` before committing
- **Tests**: add tests for every new feature; maintain 100% of existing tests

### Adding a New Input Format

The input system is designed for extension. To add support for `.docx`, for example:

**Step 1:** Add the extension to the constant in `app/input.py`:
```python
_DOCX_EXT = frozenset({".docx"})

SUPPORTED_EXTENSIONS: frozenset[str] = (
    _JSONL_EXT | _JSON_EXT | _PDF_EXT | _IMAGE_EXT | _MARKDOWN_EXT | _TEXT_EXT | _DOCX_EXT
)
```

**Step 2:** Write the reader function in the same file:
```python
def _load_docx(path: Path) -> Iterator[tuple[str, str]]:
    try:
        from docx import Document
    except ImportError as exc:
        raise ImportError("DOCX support requires python-docx: pip install python-docx") from exc

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"DOCX file not found: {path}")

    doc = Document(str(path))
    raw_text = "\n".join(para.text for para in doc.paragraphs)
    normalized = normalize_resume_text(raw_text)
    candidate_id = _make_file_id(path)
    yield candidate_id, normalized
```

**Step 3:** Add a branch to `detect_input_type()` and `dispatch()`:
```python
# In detect_input_type():
if ext in _DOCX_EXT:
    return "docx"

# In dispatch():
elif fmt == "docx":
    yield from _load_docx(path)
```

**Step 4:** Add an optional dependency to `pyproject.toml`:
```toml
[project.optional-dependencies]
docx = ["python-docx>=1.1.0"]
```

**Step 5:** Write tests in `tests/test_docx_reader.py`. No other code changes are needed.

### Adding a New Embedding Model

1. Update `configs/default.yaml` (or create a new YAML) with the new `model_name` and `vector_dimension`
2. Update `validate_embeddings()` calls in `pipeline.py` if the dimension changes
3. Run the full test suite: `pytest tests/ -v`

### Adding a New Output Format

Currently outputs NumPy `.npy`. To add Parquet, HDF5, or similar:
1. Add a new writer function in `app/io.py`
2. Call it from `pipeline.py` after `save_embeddings()`
3. Update `write_metadata()` if needed
4. Add tests in `tests/`

---

## License

MIT — see [LICENSE](LICENSE) for details.
