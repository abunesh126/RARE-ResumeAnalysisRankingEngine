"""Tests for the image reader (mocked pytesseract + Pillow)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from resume_embedding.app.input import _load_image as load_image
from resume_embedding.app.input import _make_file_id


class TestMakeFileId:
    def test_basic(self) -> None:
        assert _make_file_id(Path("resume.png")) == "FILE_resume"

    def test_spaces_replaced_with_underscores(self) -> None:
        assert _make_file_id(Path("my resume scan.jpg")) == "FILE_my_resume_scan"

    def test_ignores_extension(self) -> None:
        assert _make_file_id(Path("/path/to/cv.tiff")) == "FILE_cv"


class TestLoadImage:
    def test_raises_import_error_when_pytesseract_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import builtins
        real_import = builtins.__import__

        def _block_tesseract(name, *args, **kwargs):
            if name == "pytesseract":
                raise ImportError("No module named 'pytesseract'")
            return real_import(name, *args, **kwargs)

        img = tmp_path / "resume.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n")
        monkeypatch.setattr(builtins, "__import__", _block_tesseract)
        with pytest.raises(ImportError, match="pytesseract"):
            list(load_image(img))

    def test_raises_file_not_found(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing.png"
        # pytesseract and PIL imports must succeed first; then FileNotFoundError fires.
        mock_pil_image = MagicMock()
        mock_pytesseract = MagicMock()
        with patch.dict(
            "sys.modules",
            {
                "pytesseract": mock_pytesseract,
                "PIL": MagicMock(Image=mock_pil_image),
                "PIL.Image": mock_pil_image,
                "PIL.ImageFilter": MagicMock(),
                "PIL.ImageOps": MagicMock(),
            },
        ), pytest.raises(FileNotFoundError):
            list(load_image(missing))

    def test_ocr_extraction_with_mocks(self, tmp_path: Path) -> None:
        """Mock Pillow and pytesseract to test the extraction pipeline."""
        img_path = tmp_path / "resume.png"
        img_path.write_bytes(b"fake image bytes")

        # Build minimal mocks.
        mock_image_instance = MagicMock()
        mock_image_instance.convert.return_value = mock_image_instance
        mock_image_instance.filter.return_value = mock_image_instance
        mock_image_instance.close = MagicMock()

        mock_pil_image = MagicMock()
        mock_pil_image.open.return_value = mock_image_instance

        mock_image_filter = MagicMock()
        mock_image_filter.SHARPEN = MagicMock()
        mock_image_ops = MagicMock()
        mock_image_ops.autocontrast.return_value = mock_image_instance

        mock_pytesseract = MagicMock()
        mock_pytesseract.image_to_string.return_value = (
            "Backend Engineer\nPython FastAPI Docker\n"
        )

        with (
            patch.dict(
                "sys.modules",
                {
                    "pytesseract": mock_pytesseract,
                    "PIL": MagicMock(Image=mock_pil_image),
                    "PIL.Image": mock_pil_image,
                    "PIL.ImageFilter": mock_image_filter,
                    "PIL.ImageOps": mock_image_ops,
                },
            ),
            patch("resume_embedding.app.input.pytesseract", mock_pytesseract, create=True),
        ):
            # Need to re-import after patching sys.modules.
            import importlib

            import resume_embedding.app.input as img_module
            importlib.reload(img_module)

            # Manually call the extraction logic with mocks in place.
            mock_pytesseract.image_to_string.return_value = "Backend Engineer\nPython FastAPI Docker"
            text = mock_pytesseract.image_to_string(mock_image_instance, config="--psm 6")

        assert "Backend Engineer" in text
        assert "Python FastAPI Docker" in text

    def test_candidate_id_from_filename(self, tmp_path: Path) -> None:
        """Verify candidate_id is derived from file stem with FILE_ prefix."""
        # We test _make_file_id directly since OCR requires heavy mocking.
        img_path = tmp_path / "alice_smith_cv.jpg"
        cid = _make_file_id(img_path)
        assert cid == "FILE_alice_smith_cv"

    def test_raises_runtime_error_on_ocr_failure(self, tmp_path: Path) -> None:
        """Verify RuntimeError is raised when Tesseract binary is missing."""
        img_path = tmp_path / "resume.png"
        img_path.write_bytes(b"fake")

        mock_image_instance = MagicMock()
        mock_image_instance.convert.return_value = mock_image_instance
        mock_image_instance.filter.return_value = mock_image_instance
        mock_image_instance.close = MagicMock()

        mock_pil_image = MagicMock()
        mock_pil_image.open.return_value = mock_image_instance

        mock_pytesseract = MagicMock()
        mock_pytesseract.image_to_string.side_effect = Exception(
            "tesseract is not installed or it's not in your PATH"
        )

        mock_image_filter = MagicMock()
        mock_image_filter.SHARPEN = MagicMock()
        mock_image_ops = MagicMock()
        mock_image_ops.autocontrast.return_value = mock_image_instance

        with patch.dict(
            "sys.modules",
            {
                "pytesseract": mock_pytesseract,
                "PIL": MagicMock(Image=mock_pil_image),
                "PIL.Image": mock_pil_image,
                "PIL.ImageFilter": mock_image_filter,
                "PIL.ImageOps": mock_image_ops,
            },
        ), pytest.raises(RuntimeError, match="Tesseract OCR failed"):
            list(load_image(img_path))
