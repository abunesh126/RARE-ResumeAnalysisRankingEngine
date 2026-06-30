"""Tests for the plain text reader."""

from pathlib import Path

import pytest

from resume_embedding.app.input import _load_text as load_text


class TestLoadText:
    def test_reads_utf8_file(self, tmp_path: Path) -> None:
        txt = tmp_path / "resume.txt"
        txt.write_text("Backend Engineer\nPython FastAPI Docker", encoding="utf-8")
        results = list(load_text(txt))
        assert len(results) == 1
        cid, text = results[0]
        assert cid == "FILE_resume"
        assert "Backend Engineer" in text
        assert "Python FastAPI Docker" in text

    def test_candidate_id_uses_filename_stem(self, tmp_path: Path) -> None:
        txt = tmp_path / "john_doe_resume.txt"
        txt.write_text("Engineer", encoding="utf-8")
        cid, _ = list(load_text(txt))[0]
        assert cid == "FILE_john_doe_resume"

    def test_spaces_in_filename_become_underscores(self, tmp_path: Path) -> None:
        txt = tmp_path / "my resume.txt"
        txt.write_text("Engineer", encoding="utf-8")
        cid, _ = list(load_text(txt))[0]
        assert cid == "FILE_my_resume"

    def test_normalizes_whitespace(self, tmp_path: Path) -> None:
        txt = tmp_path / "resume.txt"
        txt.write_text("Python    FastAPI\r\n\r\nDocker", encoding="utf-8")
        _, text = list(load_text(txt))[0]
        assert "Python FastAPI" in text
        assert "\r" not in text

    def test_raises_for_missing_file(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist.txt"
        with pytest.raises(FileNotFoundError):
            list(load_text(missing))

    def test_empty_file_yields_empty_text(self, tmp_path: Path) -> None:
        txt = tmp_path / "empty.txt"
        txt.write_text("", encoding="utf-8")
        results = list(load_text(txt))
        assert len(results) == 1
        _, text = results[0]
        assert text == ""

    def test_unicode_content(self, tmp_path: Path) -> None:
        txt = tmp_path / "unicode.txt"
        txt.write_text("Développeur Python — 5 ans d'expérience", encoding="utf-8")
        _, text = list(load_text(txt))[0]
        assert "Développeur" in text
        assert "Python" in text
