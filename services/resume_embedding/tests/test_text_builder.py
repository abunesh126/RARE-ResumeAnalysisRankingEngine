"""Tests for text_builder module."""

import pytest

from resume_embedding.app.io import CandidateProfile
from resume_embedding.app.model import candidate_to_text


class TestCandidateToText:
    """Tests for the candidate_to_text function."""

    def test_full_candidate_text(self, sample_candidate: CandidateProfile) -> None:
        """Full candidate should produce text with all sections."""
        text = candidate_to_text(sample_candidate)

        assert "[CURRENT_TITLE]" in text
        assert "Backend Engineer" in text
        assert "[HEADLINE]" in text
        assert "SQL, Spark, Cloud" in text
        assert "[SUMMARY]" in text
        assert "6.9 years" in text
        assert "[SKILLS]" in text
        assert "NLP (advanced)" in text
        assert "AWS (beginner)" in text
        assert "[EXPERIENCE]" in text
        assert "Mindtree" in text
        assert "Dunder Mifflin" in text
        assert "[EDUCATION]" in text
        assert "B.E. in Computer Science" in text
        assert "Lovely Professional University" in text
        assert "[CERTIFICATIONS]" in text
        assert "AWS Certified Cloud Practitioner" in text
        assert "[LANGUAGES]" in text
        assert "English (professional)" in text
        assert "[METADATA]" in text
        assert "Toronto" in text
        assert "Canada" in text

    def test_minimal_candidate_text(self, minimal_candidate: CandidateProfile) -> None:
        """Minimal candidate should produce minimal text (no empty sections)."""
        text = candidate_to_text(minimal_candidate)

        assert "[CURRENT_TITLE]" not in text
        assert "[HEADLINE]" not in text
        assert "[SUMMARY]" not in text
        assert "[SKILLS]" not in text
        assert "[EXPERIENCE]" not in text
        assert "[EDUCATION]" not in text
        assert "[CERTIFICATIONS]" not in text

    def test_no_redrob_signals_in_text(self, sample_candidate: CandidateProfile) -> None:
        """Redrob signals should NOT appear in the text output."""
        text = candidate_to_text(sample_candidate)
        assert "profile_completeness_score" not in text
        assert "redrob" not in text.lower()
        assert "open_to_work" not in text

    def test_no_anonymized_name_in_text(self, sample_candidate: CandidateProfile) -> None:
        """Anonymized name should NOT appear in the text output."""
        text = candidate_to_text(sample_candidate)
        assert "Ira Vora" not in text

    def test_section_ordering(self, sample_candidate: CandidateProfile) -> None:
        """Sections should appear in the optimized order."""
        text = candidate_to_text(sample_candidate)
        positions = {
            "CURRENT_TITLE": text.index("[CURRENT_TITLE]"),
            "HEADLINE": text.index("[HEADLINE]"),
            "SUMMARY": text.index("[SUMMARY]"),
            "SKILLS": text.index("[SKILLS]"),
            "EXPERIENCE": text.index("[EXPERIENCE]"),
            "EDUCATION": text.index("[EDUCATION]"),
            "CERTIFICATIONS": text.index("[CERTIFICATIONS]"),
            "LANGUAGES": text.index("[LANGUAGES]"),
            "METADATA": text.index("[METADATA]"),
        }
        # Verify ordering
        ordered_keys = list(positions.keys())
        ordered_positions = [positions[k] for k in ordered_keys]
        assert ordered_positions == sorted(ordered_positions)

    def test_skills_format(self, sample_candidate: CandidateProfile) -> None:
        """Skills should be formatted as 'name (proficiency)' separated by ' | '."""
        text = candidate_to_text(sample_candidate)
        skills_section_start = text.index("[SKILLS]")
        skills_section_end = text.index("\n\n", skills_section_start)
        skills_text = text[skills_section_start:skills_section_end]
        assert " | " in skills_text

    def test_experience_duration(self, sample_candidate: CandidateProfile) -> None:
        """Experience entries should include duration in months."""
        text = candidate_to_text(sample_candidate)
        assert "27 months" in text
        assert "55 months" in text

    def test_education_format(self, sample_candidate: CandidateProfile) -> None:
        """Education should include degree, field, institution, and years."""
        text = candidate_to_text(sample_candidate)
        assert "B.E. in Computer Science" in text
        assert "from Lovely Professional University" in text
        assert "(2017-2020)" in text
        assert "8.24 CGPA" in text

    def test_returns_string(self, sample_candidate: CandidateProfile) -> None:
        """candidate_to_text should return a string."""
        text = candidate_to_text(sample_candidate)
        assert isinstance(text, str)
        assert len(text) > 0

    def test_type_error_on_invalid_input(self) -> None:
        """Should raise TypeError for non-CandidateProfile input."""
        with pytest.raises(TypeError, match="Expected CandidateProfile"):
            candidate_to_text({"candidate_id": "test"})  # type: ignore

    def test_certifications_with_issuer_and_year(self, sample_candidate: CandidateProfile) -> None:
        """Certifications should include issuer and year."""
        text = candidate_to_text(sample_candidate)
        assert "(AWS, 2025)" in text

    def test_languages_format(self, sample_candidate: CandidateProfile) -> None:
        """Languages should be formatted as 'name (proficiency)' separated by ' | '."""
        text = candidate_to_text(sample_candidate)
        assert "English (professional)" in text
        assert "Hindi (conversational)" in text
        # Check pipe separator
        languages_start = text.index("[LANGUAGES]")
        languages_end = text.index("\n\n", languages_start)
        languages_text = text[languages_start:languages_end]
        assert " | " in languages_text
