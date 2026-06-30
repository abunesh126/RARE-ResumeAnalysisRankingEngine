"""Tests for candidate_parser module."""

import json
import tempfile
from pathlib import Path

import pytest

from resume_embedding.app.io import (
    CandidateProfile,
    CareerEntry,
    CertificationEntry,
    EducationEntry,
    LanguageEntry,
    ProfileInfo,
    SkillEntry,
    load_candidates,
)


class TestCandidateProfile:
    """Tests for CandidateProfile Pydantic model."""

    def test_valid_candidate_parsing(self, sample_candidate_dict: dict) -> None:
        """Full candidate record should parse without errors."""
        candidate = CandidateProfile.model_validate(sample_candidate_dict)
        assert candidate.candidate_id == "CAND_0000001"
        assert candidate.profile.current_title == "Backend Engineer"
        assert len(candidate.career_history) == 2
        assert len(candidate.education) == 1
        assert len(candidate.skills) == 3
        assert len(candidate.certifications) == 1
        assert len(candidate.languages) == 2

    def test_minimal_candidate_parsing(self, minimal_candidate_dict: dict) -> None:
        """Minimal candidate record with empty arrays should parse."""
        candidate = CandidateProfile.model_validate(minimal_candidate_dict)
        assert candidate.candidate_id == "CAND_0000099"
        assert candidate.career_history == []
        assert candidate.education == []
        assert candidate.skills == []

    def test_candidate_id_validation(self) -> None:
        """Invalid candidate_id should raise ValidationError."""
        with pytest.raises(ValueError):
            CandidateProfile.model_validate({
                "candidate_id": "INVALID_001",
                "profile": {"anonymized_name": "Test"},
            })

    def test_profile_fields(self, sample_candidate: CandidateProfile) -> None:
        """Profile fields should be accessible and correctly typed."""
        assert isinstance(sample_candidate.profile, ProfileInfo)
        assert sample_candidate.profile.years_of_experience == 6.9
        assert sample_candidate.profile.country == "Canada"
        assert sample_candidate.profile.current_company_size == "10001+"

    def test_career_entry_fields(self, sample_candidate: CandidateProfile) -> None:
        """Career history entries should have all fields."""
        first_role = sample_candidate.career_history[0]
        assert isinstance(first_role, CareerEntry)
        assert first_role.company == "Mindtree"
        assert first_role.is_current is True
        assert first_role.duration_months == 27
        assert first_role.end_date is None

    def test_education_entry_fields(self, sample_candidate: CandidateProfile) -> None:
        """Education entries should be parsed correctly."""
        edu = sample_candidate.education[0]
        assert isinstance(edu, EducationEntry)
        assert edu.degree == "B.E."
        assert edu.field_of_study == "Computer Science"
        assert edu.start_year == 2017

    def test_skill_entry_fields(self, sample_candidate: CandidateProfile) -> None:
        """Skill entries should include proficiency and endorsements."""
        nlp_skill = sample_candidate.skills[0]
        assert isinstance(nlp_skill, SkillEntry)
        assert nlp_skill.name == "NLP"
        assert nlp_skill.proficiency == "advanced"
        assert nlp_skill.endorsements == 37

    def test_certification_entry(self, sample_candidate: CandidateProfile) -> None:
        """Certification entries should parse correctly."""
        cert = sample_candidate.certifications[0]
        assert isinstance(cert, CertificationEntry)
        assert cert.name == "AWS Certified Cloud Practitioner"
        assert cert.issuer == "AWS"
        assert cert.year == 2025

    def test_language_entry(self, sample_candidate: CandidateProfile) -> None:
        """Language entries should parse correctly."""
        lang = sample_candidate.languages[0]
        assert isinstance(lang, LanguageEntry)
        assert lang.language == "English"
        assert lang.proficiency == "professional"


class TestLoadCandidates:
    """Tests for the load_candidates streaming reader."""

    def test_load_from_jsonl(self, sample_jsonl_file: Path) -> None:
        """Should stream candidates from a JSONL file."""
        candidates = list(load_candidates(sample_jsonl_file))
        assert len(candidates) == 2
        assert candidates[0].candidate_id == "CAND_0000001"
        assert candidates[1].candidate_id == "CAND_0000099"

    def test_load_nonexistent_file(self) -> None:
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            list(load_candidates(Path("/nonexistent/file.jsonl")))

    def test_skip_invalid_records(self) -> None:
        """Should skip invalid records when skip_invalid=True."""
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        )
        tmp.write(json.dumps({"candidate_id": "CAND_0000001", "profile": {"anonymized_name": "A"}}) + "\n")
        tmp.write("THIS IS NOT JSON\n")
        tmp.write(json.dumps({"candidate_id": "CAND_0000002", "profile": {"anonymized_name": "B"}}) + "\n")
        tmp.close()

        candidates = list(load_candidates(Path(tmp.name), skip_invalid=True))
        assert len(candidates) == 2

    def test_raise_on_invalid_records(self) -> None:
        """Should raise ValueError for invalid records when skip_invalid=False."""
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        )
        tmp.write("NOT JSON\n")
        tmp.close()

        with pytest.raises(ValueError, match="Invalid record"):
            list(load_candidates(Path(tmp.name), skip_invalid=False))

    def test_skip_empty_lines(self) -> None:
        """Should skip empty lines in JSONL file."""
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        )
        tmp.write(json.dumps({"candidate_id": "CAND_0000001", "profile": {"anonymized_name": "A"}}) + "\n")
        tmp.write("\n")
        tmp.write("   \n")
        tmp.write(json.dumps({"candidate_id": "CAND_0000002", "profile": {"anonymized_name": "B"}}) + "\n")
        tmp.close()

        candidates = list(load_candidates(Path(tmp.name)))
        assert len(candidates) == 2

    def test_streaming_yields_one_at_a_time(self, sample_jsonl_file: Path) -> None:
        """Should yield candidates one at a time (iterator behavior)."""
        gen = load_candidates(sample_jsonl_file)
        first = next(gen)
        assert first.candidate_id == "CAND_0000001"
        second = next(gen)
        assert second.candidate_id == "CAND_0000099"
        with pytest.raises(StopIteration):
            next(gen)


class TestLoadCandidatesJSON:
    """Tests for loading from JSON array files (.json)."""

    def test_load_from_json_array(
        self, sample_candidate_dict: dict, minimal_candidate_dict: dict
    ) -> None:
        """Should load candidates from a JSON array file."""
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        json.dump([sample_candidate_dict, minimal_candidate_dict], tmp)
        tmp.close()

        candidates = list(load_candidates(Path(tmp.name)))
        assert len(candidates) == 2
        assert candidates[0].candidate_id == "CAND_0000001"
        assert candidates[1].candidate_id == "CAND_0000099"

    def test_skip_invalid_in_json_array(
        self, sample_candidate_dict: dict
    ) -> None:
        """Should skip invalid records in a JSON array."""
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        json.dump([sample_candidate_dict, {"bad": "record"}], tmp)
        tmp.close()

        candidates = list(load_candidates(Path(tmp.name), skip_invalid=True))
        assert len(candidates) == 1
        assert candidates[0].candidate_id == "CAND_0000001"

    def test_non_array_json_raises(self) -> None:
        """Should raise ValueError if .json file is not an array."""
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        json.dump({"not": "an array"}, tmp)
        tmp.close()

        with pytest.raises(ValueError, match="Expected a JSON array"):
            list(load_candidates(Path(tmp.name)))

    def test_unsupported_extension_raises(self) -> None:
        """Should raise ValueError for unsupported file extensions."""
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        )
        tmp.write("some,data\n")
        tmp.close()

        with pytest.raises(ValueError, match="Unsupported file extension"):
            list(load_candidates(Path(tmp.name)))
