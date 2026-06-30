"""Shared test fixtures for the resume embedding test suite."""

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from resume_embedding.app.io import CandidateProfile


@pytest.fixture
def sample_candidate_dict() -> dict:
    """Return a complete candidate record as a Python dictionary."""
    return {
        "candidate_id": "CAND_0000001",
        "profile": {
            "anonymized_name": "Ira Vora",
            "headline": "Backend Engineer | SQL, Spark, Cloud",
            "summary": "Software / data professional with 6.9 years of experience building data pipelines.",
            "location": "Toronto",
            "country": "Canada",
            "years_of_experience": 6.9,
            "current_title": "Backend Engineer",
            "current_company": "Mindtree",
            "current_company_size": "10001+",
            "current_industry": "IT Services",
        },
        "career_history": [
            {
                "company": "Mindtree",
                "title": "Backend Engineer",
                "start_date": "2024-03-08",
                "end_date": None,
                "duration_months": 27,
                "is_current": True,
                "industry": "IT Services",
                "company_size": "10001+",
                "description": "Implemented streaming data pipelines on Kafka and Spark Streaming.",
            },
            {
                "company": "Dunder Mifflin",
                "title": "Analytics Engineer",
                "start_date": "2019-07-03",
                "end_date": "2024-01-08",
                "duration_months": 55,
                "is_current": False,
                "industry": "Paper Products",
                "company_size": "201-500",
                "description": "Built and maintained data pipelines on Apache Airflow.",
            },
        ],
        "education": [
            {
                "institution": "Lovely Professional University",
                "degree": "B.E.",
                "field_of_study": "Computer Science",
                "start_year": 2017,
                "end_year": 2020,
                "grade": "8.24 CGPA",
                "tier": "tier_3",
            }
        ],
        "skills": [
            {"name": "NLP", "proficiency": "advanced", "endorsements": 37, "duration_months": 26},
            {"name": "AWS", "proficiency": "beginner", "endorsements": 5, "duration_months": 8},
            {"name": "Flask", "proficiency": "beginner", "endorsements": 15, "duration_months": 15},
        ],
        "certifications": [
            {"name": "AWS Certified Cloud Practitioner", "issuer": "AWS", "year": 2025},
        ],
        "languages": [
            {"language": "English", "proficiency": "professional"},
            {"language": "Hindi", "proficiency": "conversational"},
        ],
        "redrob_signals": {
            "profile_completeness_score": 86.9,
            "signup_date": "2025-10-16",
            "last_active_date": "2026-05-20",
            "open_to_work_flag": True,
            "profile_views_received_30d": 23,
            "applications_submitted_30d": 2,
            "recruiter_response_rate": 0.34,
            "avg_response_time_hours": 177.8,
            "skill_assessment_scores": {"NLP": 38.8},
            "connection_count": 356,
            "endorsements_received": 35,
            "notice_period_days": 60,
            "expected_salary_range_inr_lpa": {"min": 18.7, "max": 36.1},
            "preferred_work_mode": "onsite",
            "willing_to_relocate": False,
            "github_activity_score": 9.2,
            "search_appearance_30d": 249,
            "saved_by_recruiters_30d": 4,
            "interview_completion_rate": 0.71,
            "offer_acceptance_rate": 0.58,
            "verified_email": True,
            "verified_phone": True,
            "linkedin_connected": False,
        },
    }


@pytest.fixture
def sample_candidate(sample_candidate_dict: dict) -> CandidateProfile:
    """Return a parsed CandidateProfile instance."""
    return CandidateProfile.model_validate(sample_candidate_dict)


@pytest.fixture
def minimal_candidate_dict() -> dict:
    """Return a minimal valid candidate record."""
    return {
        "candidate_id": "CAND_0000099",
        "profile": {
            "anonymized_name": "Test User",
            "headline": "",
            "summary": "",
            "location": "",
            "country": "",
            "years_of_experience": 0,
            "current_title": "",
            "current_company": "",
            "current_company_size": "",
            "current_industry": "",
        },
        "career_history": [],
        "education": [],
        "skills": [],
        "redrob_signals": {
            "profile_completeness_score": 0,
            "signup_date": "2025-01-01",
            "last_active_date": "2025-01-01",
            "open_to_work_flag": False,
            "profile_views_received_30d": 0,
            "applications_submitted_30d": 0,
            "recruiter_response_rate": 0,
            "avg_response_time_hours": 0,
            "skill_assessment_scores": {},
            "connection_count": 0,
            "endorsements_received": 0,
            "notice_period_days": 0,
            "expected_salary_range_inr_lpa": {"min": 0, "max": 0},
            "preferred_work_mode": "remote",
            "willing_to_relocate": False,
            "github_activity_score": -1,
            "search_appearance_30d": 0,
            "saved_by_recruiters_30d": 0,
            "interview_completion_rate": 0,
            "offer_acceptance_rate": -1,
            "verified_email": False,
            "verified_phone": False,
            "linkedin_connected": False,
        },
    }


@pytest.fixture
def minimal_candidate(minimal_candidate_dict: dict) -> CandidateProfile:
    """Return a minimal CandidateProfile instance."""
    return CandidateProfile.model_validate(minimal_candidate_dict)


@pytest.fixture
def sample_jsonl_file(sample_candidate_dict: dict, minimal_candidate_dict: dict) -> Path:
    """Create a temporary JSONL file with two candidate records."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
    )
    tmp.write(json.dumps(sample_candidate_dict) + "\n")
    tmp.write(json.dumps(minimal_candidate_dict) + "\n")
    tmp.close()
    return Path(tmp.name)


@pytest.fixture
def sample_embeddings() -> np.ndarray:
    """Return a small set of random normalized 384-dim embeddings."""
    rng = np.random.default_rng(42)
    vectors = rng.standard_normal((5, 384)).astype(np.float32)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / norms


@pytest.fixture
def sample_candidate_ids() -> list[str]:
    """Return candidate IDs matching sample_embeddings."""
    return [f"CAND_{i:07d}" for i in range(1, 6)]


@pytest.fixture
def tmp_output_dir() -> Path:
    """Create a temporary output directory."""
    tmp = tempfile.mkdtemp(prefix="resume_embed_test_")
    return Path(tmp)
