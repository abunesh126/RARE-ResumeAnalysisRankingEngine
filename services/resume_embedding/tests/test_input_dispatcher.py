"""Tests for the input format dispatcher.

Covers:
- detect_input_type() for all supported extensions
- detect_input_type() raises ValueError for unsupported extensions
- dispatch() raises FileNotFoundError for missing files
- dispatch() raises ValueError for unsupported extension
- dispatch() correctly routes to each reader (integration-lite via tmp files)
"""

import json
from pathlib import Path

import pytest

from resume_embedding.app.input import (
    SUPPORTED_EXTENSIONS,
    detect_input_type,
    dispatch,
)

# ── detect_input_type ─────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("candidates.jsonl", "jsonl"),
        ("candidates.JSONL", "jsonl"),
        ("sample.json", "json"),
        ("sample.JSON", "json"),
        ("resume.pdf", "pdf"),
        ("resume.PDF", "pdf"),
        ("resume.png", "image"),
        ("resume.PNG", "image"),
        ("resume.jpg", "image"),
        ("resume.jpeg", "image"),
        ("resume.bmp", "image"),
        ("resume.tiff", "image"),
        ("resume.TIFF", "image"),
        ("resume.md", "markdown"),
        ("resume.MD", "markdown"),
        ("resume.txt", "text"),
        ("resume.TXT", "text"),
    ],
)
def test_detect_input_type_supported(filename: str, expected: str) -> None:
    assert detect_input_type(Path(filename)) == expected


@pytest.mark.parametrize(
    "filename",
    ["resume.docx", "resume.xlsx", "resume.csv", "resume.html", "resume"],
)
def test_detect_input_type_unsupported_raises(filename: str) -> None:
    with pytest.raises(ValueError, match="Unsupported file extension"):
        detect_input_type(Path(filename))


def test_supported_extensions_set() -> None:
    """All advertised extensions must be present in SUPPORTED_EXTENSIONS."""
    expected = {
        ".jsonl", ".json", ".pdf",
        ".png", ".jpg", ".jpeg", ".bmp", ".tiff",
        ".md", ".txt",
    }
    assert expected == SUPPORTED_EXTENSIONS


# ── dispatch: error cases ─────────────────────────────────────────────────────


def test_dispatch_missing_file_raises(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist.txt"
    with pytest.raises(FileNotFoundError):
        list(dispatch(missing))


def test_dispatch_unsupported_extension_raises(tmp_path: Path) -> None:
    bad = tmp_path / "resume.docx"
    bad.write_text("content")
    with pytest.raises(ValueError, match="Unsupported file extension"):
        list(dispatch(bad))


# ── dispatch: .txt routing ────────────────────────────────────────────────────


def test_dispatch_txt(tmp_path: Path) -> None:
    txt = tmp_path / "john_doe.txt"
    txt.write_text("Backend Engineer\nPython FastAPI Docker", encoding="utf-8")
    results = list(dispatch(txt))
    assert len(results) == 1
    cid, text = results[0]
    assert cid == "FILE_john_doe"
    assert "Backend Engineer" in text
    assert "Python" in text


# ── dispatch: .md routing ─────────────────────────────────────────────────────


def test_dispatch_md(tmp_path: Path) -> None:
    md = tmp_path / "resume_jane.md"
    md.write_text("# Jane Smith\n\n## Skills\n- Python\n- Docker", encoding="utf-8")
    results = list(dispatch(md))
    assert len(results) == 1
    cid, text = results[0]
    assert cid == "FILE_resume_jane"
    assert "Jane Smith" in text
    assert "Python" in text
    # Markdown syntax should be stripped
    assert "##" not in text
    assert "- Python" not in text


# ── dispatch: .json routing (structured) ─────────────────────────────────────


def test_dispatch_json(tmp_path: Path, sample_candidate_dict: dict) -> None:
    """dispatch() on a .json file yields one tuple per valid record."""
    json_file = tmp_path / "candidates.json"
    json_file.write_bytes(json.dumps([sample_candidate_dict]).encode())
    results = list(dispatch(json_file))
    assert len(results) == 1
    cid, text = results[0]
    assert cid == sample_candidate_dict["candidate_id"]
    assert "[CURRENT_TITLE]" in text


# ── dispatch: .jsonl routing (structured) ────────────────────────────────────


def test_dispatch_jsonl(tmp_path: Path, sample_candidate_dict: dict) -> None:
    """dispatch() on a .jsonl file yields one tuple per valid record."""
    jsonl_file = tmp_path / "candidates.jsonl"
    jsonl_file.write_bytes(json.dumps(sample_candidate_dict).encode() + b"\n")
    results = list(dispatch(jsonl_file))
    assert len(results) == 1
    cid, text = results[0]
    assert cid == sample_candidate_dict["candidate_id"]
    assert "[CURRENT_TITLE]" in text


# ── dispatch: .pdf routing (mocked) ──────────────────────────────────────────


def test_dispatch_pdf_missing_pymupdf(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """dispatch() raises ImportError when PyMuPDF is not installed."""
    import builtins
    real_import = builtins.__import__

    def _block_fitz(name, *args, **kwargs):
        if name == "fitz":
            raise ImportError("No module named 'fitz'")
        return real_import(name, *args, **kwargs)

    pdf = tmp_path / "resume.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    monkeypatch.setattr(builtins, "__import__", _block_fitz)
    with pytest.raises(ImportError, match="PyMuPDF"):
        list(dispatch(pdf))


# ── dispatch: image routing (mocked) ─────────────────────────────────────────


def test_dispatch_image_missing_pytesseract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """dispatch() raises ImportError when pytesseract is not installed."""
    import builtins
    real_import = builtins.__import__

    def _block_tesseract(name, *args, **kwargs):
        if name == "pytesseract":
            raise ImportError("No module named 'pytesseract'")
        return real_import(name, *args, **kwargs)

    img = tmp_path / "resume.png"
    # Write a minimal valid PNG (1x1 white pixel).
    img.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
        b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    monkeypatch.setattr(builtins, "__import__", _block_tesseract)
    with pytest.raises(ImportError, match="pytesseract"):
        list(dispatch(img))
