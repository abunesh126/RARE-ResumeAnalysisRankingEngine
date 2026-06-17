# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-06-17

### Added
- YAML configuration support (`configs/default.yaml`, `configs/model.yaml`)
- Checkpoint and resume system (`--resume` flag)
- GPU auto-detection (torch + onnxruntime CUDA check)
- `--device` CLI flag (`auto`, `cuda`, `cpu`)
- `--config` CLI flag for custom YAML configs
- Timestamped output directories (`outputs/run_YYYYMMDD_HHMMSS/`)
- File logging to `outputs/.../logs/`
- Metadata fields: `device`, `timestamp`, `input_file`
- Sample dataset (`datasets/sample/sample_candidates.jsonl` — 10 records)
- Convenience scripts: `run_sample.py`, `run_dataset.py`, `benchmark.py`
- New test suites: `test_checkpoint.py`, `test_config_yaml.py`
- Comprehensive README with architecture, scope, model rationale, and roadmap

### Changed
- **BREAKING:** `run_pipeline(dataset_path=...)` → `run_pipeline(input_path=...)`
  - Now takes a JSONL file path directly instead of a directory
- `metadata.json` field `total_candidates` → `records_processed`
- CLI `--output` defaults to auto-timestamped directory instead of `./outputs`
- Bumped to `pydantic>=2.7.0`, added `pyyaml>=6.0`

### Removed
- Hardcoded dataset path in `PipelineSettings`

## [1.0.0] - 2026-06-16

### Added
- Initial embedding pipeline
- Pydantic schema validation for candidate profiles
- Section-based text builder with semantic ordering
- FastEmbed inference with BAAI/bge-small-en-v1.5
- L2 normalization and validation
- NumPy storage (`embeddings.npy`, `candidate_ids.npy`)
- Metadata writer (`metadata.json`)
- 65+ unit and integration tests
