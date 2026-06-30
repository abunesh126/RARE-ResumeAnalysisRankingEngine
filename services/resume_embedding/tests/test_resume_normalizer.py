"""Tests for resume_normalizer.normalize_resume_text()."""

import pytest

from resume_embedding.app.input import normalize_resume_text


class TestNormalizeResumeText:
    def test_empty_string_returns_empty(self) -> None:
        assert normalize_resume_text("") == ""

    def test_whitespace_only_returns_empty(self) -> None:
        assert normalize_resume_text("   \n\t  ") == ""

    def test_type_error_on_non_string(self) -> None:
        with pytest.raises(TypeError):
            normalize_resume_text(123)  # type: ignore[arg-type]

    def test_strips_outer_whitespace(self) -> None:
        result = normalize_resume_text("  hello  ")
        assert result == "hello"

    def test_normalizes_crlf_line_endings(self) -> None:
        result = normalize_resume_text("line1\r\nline2\r\nline3")
        assert "\r" not in result
        assert result == "line1\nline2\nline3"

    def test_normalizes_cr_only_line_endings(self) -> None:
        result = normalize_resume_text("line1\rline2")
        assert "\r" not in result
        assert result == "line1\nline2"

    def test_collapses_multiple_spaces(self) -> None:
        result = normalize_resume_text("Python    FastAPI     Docker")
        assert result == "Python FastAPI Docker"

    def test_collapses_tabs_to_space(self) -> None:
        result = normalize_resume_text("skill1\t\tskill2")
        assert result == "skill1 skill2"

    def test_collapses_triple_plus_newlines_to_double(self) -> None:
        result = normalize_resume_text("section1\n\n\n\n\nsection2")
        assert "\n\n\n" not in result
        assert "section1" in result
        assert "section2" in result

    def test_removes_separator_lines_dashes(self) -> None:
        text = "Name: John\n---\nSkills: Python"
        result = normalize_resume_text(text)
        assert "---" not in result
        assert "John" in result
        assert "Python" in result

    def test_removes_separator_lines_equals(self) -> None:
        text = "Name: John\n===\nSkills: Python"
        result = normalize_resume_text(text)
        assert "===" not in result

    def test_removes_separator_lines_underscores(self) -> None:
        text = "Name: John\n___\nSkills: Python"
        result = normalize_resume_text(text)
        assert "___" not in result

    def test_removes_control_characters(self) -> None:
        text = "Python\x00Developer\x07"
        result = normalize_resume_text(text)
        assert "\x00" not in result
        assert "\x07" not in result
        assert "Python" in result
        assert "Developer" in result

    def test_preserves_tabs_in_content_as_space(self) -> None:
        result = normalize_resume_text("col1\tcol2")
        # Tabs within lines are collapsed to space.
        assert result == "col1 col2"

    def test_real_resume_text(self) -> None:
        """Smoke test with realistic resume-like text."""
        text = (
            "  Backend Engineer  \n\n"
            "---\n\n"
            "Skills:  Python   FastAPI   Docker\r\n"
            "\n\n\n"
            "Experience:\n"
            "  Company A — 2 years\n"
        )
        result = normalize_resume_text(text)
        assert "Backend Engineer" in result
        assert "Python FastAPI Docker" in result
        assert "Company A" in result
        assert "---" not in result
        assert "\r" not in result
