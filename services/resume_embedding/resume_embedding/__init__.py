"""Resume Embedding Pipeline.

This top-level package re-exports from resume_embedding.app
for backward compatibility and programmatic access.

Supported input formats (auto-detected by file extension):
    .jsonl, .json  — Structured candidate records (Pydantic-validated)
    .pdf           — PDF resumes (requires PyMuPDF)
    .png, .jpg, .jpeg, .bmp, .tiff — Resume images (requires pytesseract + Pillow)
    .md            — Markdown resumes
    .txt           — Plain text resumes
"""

from resume_embedding.app.config import PipelineSettings
from resume_embedding.app.input import detect_input_type, dispatch
from resume_embedding.app.io import load_candidates, load_embeddings, save_embeddings
from resume_embedding.app.model import candidate_to_text, generate_embeddings, l2_normalize
from resume_embedding.app.pipeline import run_pipeline

__all__ = [
    "run_pipeline",
    "load_candidates",
    "candidate_to_text",
    "generate_embeddings",
    "l2_normalize",
    "save_embeddings",
    "load_embeddings",
    "PipelineSettings",
    "dispatch",
    "detect_input_type",
]
