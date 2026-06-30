"""Tests for the markdown reader."""

from pathlib import Path

import pytest

from resume_embedding.app.input import _load_markdown as load_markdown
from resume_embedding.app.input import _strip_markdown


class TestStripMarkdown:
    def test_strips_atx_headings(self) -> None:
        text = "# Title\n## Section\n### Sub"
        result = _strip_markdown(text)
        assert "#" not in result
        assert "Title" in result
        assert "Section" in result
        assert "Sub" in result

    def test_strips_bold_asterisks(self) -> None:
        result = _strip_markdown("**Python** developer")
        assert "**" not in result
        assert "Python" in result

    def test_strips_bold_underscores(self) -> None:
        result = _strip_markdown("__Python__ developer")
        assert "__" not in result
        assert "Python" in result

    def test_strips_italic_asterisks(self) -> None:
        result = _strip_markdown("*Senior* engineer")
        assert "Senior" in result

    def test_strips_inline_code(self) -> None:
        result = _strip_markdown("Uses `Python` and `Docker`")
        assert "`" not in result
        assert "Python" in result
        assert "Docker" in result

    def test_strips_fenced_code_blocks(self) -> None:
        text = "Skills:\n```python\nimport fastapi\n```\nMore text"
        result = _strip_markdown(text)
        assert "```" not in result
        assert "import fastapi" not in result
        assert "More text" in result

    def test_strips_links_keeps_text(self) -> None:
        result = _strip_markdown("[My GitHub](https://github.com/user)")
        assert "https://" not in result
        assert "My GitHub" in result

    def test_strips_images_entirely(self) -> None:
        result = _strip_markdown("![Profile photo](photo.png)")
        assert "![" not in result
        assert "photo.png" not in result

    def test_strips_unordered_list_markers(self) -> None:
        text = "- Python\n* Docker\n+ FastAPI"
        result = _strip_markdown(text)
        assert "Python" in result
        assert "Docker" in result
        assert "FastAPI" in result
        # List markers should be stripped
        lines = [ln.strip() for ln in result.split("\n") if ln.strip()]
        assert not any(line.startswith("- ") or line.startswith("* ") for line in lines)

    def test_strips_ordered_list_markers(self) -> None:
        text = "1. First\n2. Second\n3. Third"
        result = _strip_markdown(text)
        assert "First" in result
        assert "Second" in result

    def test_strips_blockquotes(self) -> None:
        result = _strip_markdown("> This is a quote")
        assert ">" not in result
        assert "This is a quote" in result

    def test_strips_html_tags(self) -> None:
        result = _strip_markdown("<b>Bold</b> and <i>italic</i>")
        assert "<b>" not in result
        assert "Bold" in result
        assert "italic" in result


class TestLoadMarkdown:
    def test_basic_resume(self, tmp_path: Path) -> None:
        md = tmp_path / "resume.md"
        md.write_text(
            "# Jane Doe\n\n## Summary\nPython developer with 5 years experience.\n\n"
            "## Skills\n- Python\n- Docker\n- FastAPI",
            encoding="utf-8",
        )
        results = list(load_markdown(md))
        assert len(results) == 1
        cid, text = results[0]
        assert cid == "FILE_resume"
        assert "Jane Doe" in text
        assert "Python" in text
        assert "Docker" in text
        # Markdown syntax removed
        assert "##" not in text
        assert "- Python" not in text

    def test_candidate_id_from_filename(self, tmp_path: Path) -> None:
        md = tmp_path / "john_smith_resume.md"
        md.write_text("# John Smith", encoding="utf-8")
        cid, _ = list(load_markdown(md))[0]
        assert cid == "FILE_john_smith_resume"

    def test_raises_for_missing_file(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing.md"
        with pytest.raises(FileNotFoundError):
            list(load_markdown(missing))

    def test_yields_empty_text_for_empty_file(self, tmp_path: Path) -> None:
        md = tmp_path / "empty.md"
        md.write_text("", encoding="utf-8")
        results = list(load_markdown(md))
        assert len(results) == 1
        _, text = results[0]
        assert text == ""

    def test_complex_resume_markdown(self, tmp_path: Path) -> None:
        content = """\
# Alice Engineering

## Experience

**Senior Backend Engineer** at *Acme Corp* (2020–2024)
- Built REST APIs with FastAPI
- Managed PostgreSQL databases

## Education

B.Tech in Computer Science from IIT Delhi (2016–2020)

## Certifications

1. AWS Certified Solutions Architect
2. GCP Professional Data Engineer
"""
        md = tmp_path / "alice.md"
        md.write_text(content, encoding="utf-8")
        _, text = list(load_markdown(md))[0]

        assert "Alice Engineering" in text
        assert "Senior Backend Engineer" in text
        assert "Acme Corp" in text
        assert "FastAPI" in text
        assert "IIT Delhi" in text
        assert "AWS Certified Solutions Architect" in text
        # Markdown syntax removed
        assert "**" not in text
        assert "*Acme" not in text
        assert "##" not in text
