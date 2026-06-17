"""Candidate profile Pydantic models and streaming JSONL reader.

This module defines the data models derived from the candidate_schema.json
and provides a memory-efficient streaming reader for large JSONL files.
"""

import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Optional

import orjson
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class ProfileInfo(BaseModel):
    """Top-level profile information for a candidate.

    Contains identity, title, summary, location, and current employment details.
    """

    anonymized_name: str = Field(description="Anonymized full name.")
    headline: str = Field(default="", description="One-line professional headline.")
    summary: str = Field(default="", description="Multi-sentence professional summary.")
    location: str = Field(default="", description="City, region/state.")
    country: str = Field(default="", description="Country.")
    years_of_experience: float = Field(default=0.0, ge=0, le=50, description="Total years of experience.")
    current_title: str = Field(default="", description="Current job title.")
    current_company: str = Field(default="", description="Current employer.")
    current_company_size: str = Field(default="", description="Company size bucket.")
    current_industry: str = Field(default="", description="Current industry.")


class CareerEntry(BaseModel):
    """A single career history entry.

    Represents one role in the candidate's work history.
    """

    company: str = Field(description="Company name.")
    title: str = Field(description="Job title.")
    start_date: str = Field(default="", description="Start date (YYYY-MM-DD).")
    end_date: Optional[str] = Field(default=None, description="End date or null if current.")
    duration_months: int = Field(default=0, ge=0, description="Duration in months.")
    is_current: bool = Field(default=False, description="Whether this is the current role.")
    industry: str = Field(default="", description="Industry of the employer.")
    company_size: str = Field(default="", description="Company size bucket.")
    description: str = Field(default="", description="Role responsibilities and achievements.")


class EducationEntry(BaseModel):
    """A single education record.

    Represents one degree or educational program.
    """

    institution: str = Field(description="Institution name.")
    degree: str = Field(default="", description="Degree type (B.Tech, M.Sc, etc.).")
    field_of_study: str = Field(default="", description="Field of study / major.")
    start_year: int = Field(default=0, ge=0, description="Start year.")
    end_year: int = Field(default=0, ge=0, description="End year.")
    grade: Optional[str] = Field(default=None, description="GPA / percentage / class.")
    tier: Optional[str] = Field(default=None, description="Institution prestige tier.")


class SkillEntry(BaseModel):
    """A single skill record.

    Includes proficiency level and endorsement count.
    """

    name: str = Field(description="Skill name.")
    proficiency: str = Field(default="", description="Proficiency level.")
    endorsements: int = Field(default=0, ge=0, description="Number of endorsements.")
    duration_months: Optional[int] = Field(default=None, ge=0, description="Months of experience with this skill.")


class CertificationEntry(BaseModel):
    """A single certification record."""

    name: str = Field(description="Certification name.")
    issuer: str = Field(default="", description="Issuing organization.")
    year: int = Field(default=0, ge=0, description="Year obtained.")


class LanguageEntry(BaseModel):
    """A single language proficiency record."""

    language: str = Field(description="Language name.")
    proficiency: str = Field(default="", description="Proficiency level.")


class SalaryRange(BaseModel):
    """Expected salary range in INR Lakhs Per Annum."""

    min: float = Field(default=0.0, ge=0, description="Minimum expected salary (LPA).")
    max: float = Field(default=0.0, ge=0, description="Maximum expected salary (LPA).")


class RedrobSignals(BaseModel):
    """Platform behavioral and engagement signals.

    These are numeric/boolean metrics from the Redrob ecosystem.
    Excluded from text embedding but preserved for downstream ranking teams.
    """

    profile_completeness_score: float = Field(default=0.0)
    signup_date: str = Field(default="")
    last_active_date: str = Field(default="")
    open_to_work_flag: bool = Field(default=False)
    profile_views_received_30d: int = Field(default=0)
    applications_submitted_30d: int = Field(default=0)
    recruiter_response_rate: float = Field(default=0.0)
    avg_response_time_hours: float = Field(default=0.0)
    skill_assessment_scores: dict[str, float] = Field(default_factory=dict)
    connection_count: int = Field(default=0)
    endorsements_received: int = Field(default=0)
    notice_period_days: int = Field(default=0)
    expected_salary_range_inr_lpa: SalaryRange = Field(default_factory=SalaryRange)
    preferred_work_mode: str = Field(default="")
    willing_to_relocate: bool = Field(default=False)
    github_activity_score: float = Field(default=-1.0)
    search_appearance_30d: int = Field(default=0)
    saved_by_recruiters_30d: int = Field(default=0)
    interview_completion_rate: float = Field(default=0.0)
    offer_acceptance_rate: float = Field(default=-1.0)
    verified_email: bool = Field(default=False)
    verified_phone: bool = Field(default=False)
    linkedin_connected: bool = Field(default=False)


class CandidateProfile(BaseModel):
    """Complete candidate profile as stored in candidates.jsonl.

    This is the top-level model representing one JSONL line.
    All fields use defaults so partial records can still be parsed.
    """

    candidate_id: str = Field(description="Unique identifier (CAND_XXXXXXX).")
    profile: ProfileInfo = Field(default_factory=ProfileInfo)
    career_history: list[CareerEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    skills: list[SkillEntry] = Field(default_factory=list)
    certifications: list[CertificationEntry] = Field(default_factory=list)
    languages: list[LanguageEntry] = Field(default_factory=list)
    redrob_signals: RedrobSignals = Field(default_factory=RedrobSignals)

    @field_validator("candidate_id")
    @classmethod
    def validate_candidate_id(cls, v: str) -> str:
        """Ensure candidate_id matches the expected pattern."""
        if not v.startswith("CAND_"):
            raise ValueError(f"candidate_id must start with 'CAND_', got: {v!r}")
        return v


def load_candidates(
    input_path: Path,
    *,
    skip_invalid: bool = True,
) -> Iterator[CandidateProfile]:
    """Stream candidate profiles from a JSONL or JSON file.

    Auto-detects format by file extension:
    - ``.jsonl`` — one JSON object per line (streaming, memory-efficient)
    - ``.json``  — JSON array of objects (loaded into memory)

    Invalid records are logged and skipped when skip_invalid is True.

    Args:
        input_path: Path to the candidates file (.jsonl or .json).
        skip_invalid: If True, log and skip invalid records instead of raising.

    Yields:
        CandidateProfile instances, one per valid record.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If skip_invalid is False and a record fails validation,
            or if the file extension is unsupported.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    ext = input_path.suffix.lower()
    if ext == ".json":
        yield from _load_json_array(input_path, skip_invalid=skip_invalid)
    elif ext == ".jsonl":
        yield from _load_jsonl(input_path, skip_invalid=skip_invalid)
    else:
        raise ValueError(
            f"Unsupported file extension '{ext}'. Use .jsonl or .json."
        )


def _load_jsonl(
    jsonl_path: Path,
    *,
    skip_invalid: bool = True,
) -> Iterator[CandidateProfile]:
    """Stream candidate profiles from a JSONL file (one record per line)."""
    error_count = 0
    line_number = 0

    with open(jsonl_path, "rb") as fh:
        for raw_line in fh:
            line_number += 1
            raw_line = raw_line.strip()
            if not raw_line:
                continue

            try:
                data = orjson.loads(raw_line)
                candidate = CandidateProfile.model_validate(data)
                yield candidate
            except Exception as exc:
                error_count += 1
                if skip_invalid:
                    logger.warning(
                        "Skipping invalid record at line %d: %s",
                        line_number,
                        str(exc)[:200],
                    )
                else:
                    raise ValueError(
                        f"Invalid record at line {line_number}: {exc}"
                    ) from exc

    if error_count > 0:
        logger.info(
            "Finished reading %s: %d lines processed, %d errors skipped.",
            jsonl_path.name,
            line_number,
            error_count,
        )


def _load_json_array(
    json_path: Path,
    *,
    skip_invalid: bool = True,
) -> Iterator[CandidateProfile]:
    """Load candidate profiles from a JSON array file."""
    raw = json_path.read_bytes()
    records = orjson.loads(raw)

    if not isinstance(records, list):
        raise ValueError(
            f"Expected a JSON array in {json_path.name}, got {type(records).__name__}."
        )

    error_count = 0
    for idx, data in enumerate(records):
        try:
            candidate = CandidateProfile.model_validate(data)
            yield candidate
        except Exception as exc:
            error_count += 1
            if skip_invalid:
                logger.warning(
                    "Skipping invalid record at index %d: %s",
                    idx,
                    str(exc)[:200],
                )
            else:
                raise ValueError(
                    f"Invalid record at index {idx}: {exc}"
                ) from exc

    if error_count > 0:
        logger.info(
            "Finished reading %s: %d records processed, %d errors skipped.",
            json_path.name,
            len(records),
            error_count,
        )

