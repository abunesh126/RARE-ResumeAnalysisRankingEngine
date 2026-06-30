"""Tests for the PDF reader (mocked PyMuPDF)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from resume_embedding.app.input import _load_pdf as load_pdf
from resume_embedding.app.input import _make_file_id


class TestMakeFileId:
    def test_basic(self) -> None:
        assert _make_file_id(Path("resume.pdf")) == "FILE_resume"

    def test_spaces_replaced_with_underscores(self) -> None:
        assert _make_file_id(Path("john doe resume.pdf")) == "FILE_john_doe_resume"

    def test_ignores_extension(self) -> None:
        assert _make_file_id(Path("/some/path/my_cv.pdf")) == "FILE_my_cv"


class TestLoadPdf:
    def test_raises_import_error_when_fitz_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
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
            list(load_pdf(pdf))

    def test_raises_file_not_found(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing.pdf"
        # fitz import must succeed first; only then does the FileNotFoundError fire.
        mock_fitz = MagicMock()
        with patch.dict("sys.modules", {"fitz": mock_fitz}), pytest.raises(FileNotFoundError):
            list(load_pdf(missing))

    def test_extracts_text_from_pages(self, tmp_path: Path) -> None:
        """Mock fitz to return multi-page text and verify extraction."""
        pdf = tmp_path / "resume.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")

        page1 = MagicMock()
        page1.get_text.return_value = "Backend Engineer\nPython FastAPI"
        page2 = MagicMock()
        page2.get_text.return_value = "Company A — 2 years experience"

        mock_doc = MagicMock()
        mock_doc.__iter__ = MagicMock(return_value=iter([page1, page2]))
        mock_doc.close = MagicMock()

        mock_fitz = MagicMock()
        mock_fitz.open.return_value = mock_doc

        with patch.dict("sys.modules", {"fitz": mock_fitz}):
            results = list(load_pdf(pdf))

        assert len(results) == 1
        cid, text = results[0]
        assert cid == "FILE_resume"
        assert "Backend Engineer" in text
        assert "Python FastAPI" in text
        assert "Company A" in text

    def test_skips_empty_pages(self, tmp_path: Path) -> None:
        """Empty pages should not contribute to the extracted text."""
        pdf = tmp_path / "resume.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")

        page1 = MagicMock()
        page1.get_text.return_value = "Real content here"
        page2 = MagicMock()
        page2.get_text.return_value = "   \n\t  "  # Whitespace only

        mock_doc = MagicMock()
        mock_doc.__iter__ = MagicMock(return_value=iter([page1, page2]))
        mock_doc.close = MagicMock()

        mock_fitz = MagicMock()
        mock_fitz.open.return_value = mock_doc

        with patch.dict("sys.modules", {"fitz": mock_fitz}):
            _, text = list(load_pdf(pdf))[0]

        assert "Real content here" in text

    def test_candidate_id_from_filename(self, tmp_path: Path) -> None:
        pdf = tmp_path / "john_doe_cv.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")

        page = MagicMock()
        page.get_text.return_value = "Engineer"
        mock_doc = MagicMock()
        mock_doc.__iter__ = MagicMock(return_value=iter([page]))
        mock_doc.close = MagicMock()
        mock_fitz = MagicMock()
        mock_fitz.open.return_value = mock_doc

        with patch.dict("sys.modules", {"fitz": mock_fitz}):
            cid, _ = list(load_pdf(pdf))[0]

        assert cid == "FILE_john_doe_cv"

    def test_raises_runtime_error_on_open_failure(self, tmp_path: Path) -> None:
        pdf = tmp_path / "bad.pdf"
        pdf.write_bytes(b"not a pdf")

        mock_fitz = MagicMock()
        mock_fitz.open.side_effect = Exception("corrupt PDF")

        with patch.dict("sys.modules", {"fitz": mock_fitz}), pytest.raises(RuntimeError, match="Could not open PDF"):
                list(load_pdf(pdf))
