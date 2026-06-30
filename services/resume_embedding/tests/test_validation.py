"""Validation tests for embedding requirements.

Verifies the core constraints:
1. Vector dimension == 384
2. L2 norm == 1.0 for all vectors
3. dtype == float32
4. Candidate ID alignment
"""

import json
import tempfile
from pathlib import Path

import numpy as np

from resume_embedding.app.model import validate_embeddings
from resume_embedding.app.pipeline import run_pipeline


def _make_test_jsonl(n: int) -> Path:
    """Create a temporary dataset directory with n candidates."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="validation_test_"))
    jsonl_path = tmp_dir / "candidates.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as fh:
        for i in range(1, n + 1):
            record = {
                "candidate_id": f"CAND_{i:07d}",
                "profile": {
                    "anonymized_name": f"User {i}",
                    "headline": f"Engineer {i}",
                    "summary": f"Description for user {i}.",
                    "location": "City",
                    "country": "Country",
                    "years_of_experience": float(i),
                    "current_title": "Engineer",
                    "current_company": "Corp",
                    "current_company_size": "51-200",
                    "current_industry": "Tech",
                },
                "career_history": [{
                    "company": "Corp",
                    "title": "Engineer",
                    "start_date": "2023-01-01",
                    "end_date": None,
                    "duration_months": 12,
                    "is_current": True,
                    "industry": "Tech",
                    "company_size": "51-200",
                    "description": "Work description.",
                }],
                "education": [{
                    "institution": "University",
                    "degree": "B.Tech",
                    "field_of_study": "CS",
                    "start_year": 2015,
                    "end_year": 2019,
                }],
                "skills": [
                    {"name": "Python", "proficiency": "advanced", "endorsements": 5},
                ],
                "redrob_signals": {
                    "profile_completeness_score": 70,
                    "signup_date": "2025-01-01",
                    "last_active_date": "2026-01-01",
                    "open_to_work_flag": True,
                    "profile_views_received_30d": 5,
                    "applications_submitted_30d": 1,
                    "recruiter_response_rate": 0.5,
                    "avg_response_time_hours": 24,
                    "skill_assessment_scores": {},
                    "connection_count": 50,
                    "endorsements_received": 5,
                    "notice_period_days": 30,
                    "expected_salary_range_inr_lpa": {"min": 10, "max": 20},
                    "preferred_work_mode": "hybrid",
                    "willing_to_relocate": True,
                    "github_activity_score": 30,
                    "search_appearance_30d": 10,
                    "saved_by_recruiters_30d": 1,
                    "interview_completion_rate": 0.8,
                    "offer_acceptance_rate": 0.7,
                    "verified_email": True,
                    "verified_phone": True,
                    "linkedin_connected": True,
                },
            }
            fh.write(json.dumps(record) + "\n")
    return jsonl_path


class TestVectorDimensionValidation:
    """Validate that output embeddings have exactly 384 dimensions."""

    def test_dimension_384(self) -> None:
        """Pipeline output must have dimension 384."""
        dataset_dir = _make_test_jsonl(3)
        output_dir = Path(tempfile.mkdtemp())
        run_pipeline(input_path=dataset_dir, output_path=output_dir)

        embeddings = np.load(output_dir / "embeddings.npy")
        assert embeddings.shape[1] == 384, (
            f"Expected dimension 384, got {embeddings.shape[1]}"
        )


class TestL2NormValidation:
    """Validate that all vectors have L2 norm == 1.0."""

    def test_all_vectors_unit_norm(self) -> None:
        """Every embedding vector must have L2 norm approximately 1.0."""
        dataset_dir = _make_test_jsonl(5)
        output_dir = Path(tempfile.mkdtemp())
        run_pipeline(input_path=dataset_dir, output_path=output_dir)

        embeddings = np.load(output_dir / "embeddings.npy")
        norms = np.linalg.norm(embeddings, axis=1)

        for i, norm in enumerate(norms):
            assert abs(norm - 1.0) < 1e-5, (
                f"Vector at index {i} has L2 norm {norm:.8f}, expected 1.0"
            )

    def test_validate_embeddings_passes(self) -> None:
        """validate_embeddings should pass for pipeline output."""
        dataset_dir = _make_test_jsonl(3)
        output_dir = Path(tempfile.mkdtemp())
        run_pipeline(input_path=dataset_dir, output_path=output_dir)

        embeddings = np.load(output_dir / "embeddings.npy")
        assert validate_embeddings(embeddings) is True


class TestDtypeValidation:
    """Validate that embeddings are stored as float32."""

    def test_float32_dtype(self) -> None:
        """Embeddings must be float32."""
        dataset_dir = _make_test_jsonl(3)
        output_dir = Path(tempfile.mkdtemp())
        run_pipeline(input_path=dataset_dir, output_path=output_dir)

        embeddings = np.load(output_dir / "embeddings.npy")
        assert embeddings.dtype == np.float32


class TestCandidateIdAlignment:
    """Validate that candidate IDs align with embeddings."""

    def test_id_count_matches_embedding_count(self) -> None:
        """Number of IDs must equal number of embedding rows."""
        n = 7
        dataset_dir = _make_test_jsonl(n)
        output_dir = Path(tempfile.mkdtemp())
        run_pipeline(input_path=dataset_dir, output_path=output_dir)

        embeddings = np.load(output_dir / "embeddings.npy")
        ids = np.load(output_dir / "candidate_ids.npy")

        assert len(ids) == embeddings.shape[0] == n

    def test_id_order_preserved(self) -> None:
        """Candidate IDs must be in the same order as in the JSONL file."""
        n = 5
        dataset_dir = _make_test_jsonl(n)
        output_dir = Path(tempfile.mkdtemp())
        run_pipeline(input_path=dataset_dir, output_path=output_dir)

        ids = np.load(output_dir / "candidate_ids.npy")
        expected = [f"CAND_{i:07d}" for i in range(1, n + 1)]
        assert list(ids) == expected
