# Contributing

Thanks for your interest in contributing to the Resume Embedding Engine.

## Development Setup

```bash
git clone https://github.com/<your-username>/resume-embedding-engine.git
cd resume-embedding-engine

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/ -v
```

All 91 tests must pass before submitting a PR.

## Code Style

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
ruff check src/ tests/
ruff format src/ tests/
```

Configuration is in `pyproject.toml` under `[tool.ruff]`.

## Project Structure

- **`src/resume_embedding/`** — Core pipeline code
- **`tests/`** — Unit and integration tests
- **`scripts/`** — CLI convenience scripts
- **`configs/`** — YAML configuration files
- **`datasets/sample/`** — Bundled test data

## Pull Request Guidelines

1. Fork the repo and create a feature branch from `main`
2. Add tests for any new functionality
3. Make sure all tests pass: `pytest tests/ -v`
4. Run the linter: `ruff check src/ tests/`
5. Update `CHANGELOG.md` if the change is user-facing
6. Keep PRs focused — one feature or fix per PR

## Reporting Issues

Open an issue with:
- What you expected to happen
- What actually happened
- Steps to reproduce
- Python version and OS
