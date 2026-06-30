"""Integration tests for the full embedding pipeline."""

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from resume_embedding.app.pipeline import run_pipeline


def _create_test_jsonl(num_candidates: int) -> Path:
    """Create a temporary JSONL file with synthetic candidates.

    Args:
        num_candidates: Number of candidate records to generate.

    Returns:
        Path to the temporary JSONL file.
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="pipeline_test_"))
    jsonl_path = tmp_dir / "candidates.jsonl"

    with open(jsonl_path, "w", encoding="utf-8") as fh:
        for i in range(1, num_candidates + 1):
            candidate = {
                "candidate_id": f"CAND_{i:07d}",
                "profile": {
                    "anonymized_name": f"Test User {i}",
                    "headline": f"Software Engineer #{i}",
                    "summary": f"Developer with {i} years of experience in Python and ML.",
                    "location": "Bangalore",
                    "country": "India",
                    "years_of_experience": float(i),
                    "current_title": "Software Engineer",
                    "current_company": f"Company {i}",
                    "current_company_size": "51-200",
                    "current_industry": "Software",
                },
                "career_history": [
                    {
                        "company": f"Company {i}",
                        "title": "Software Engineer",
                        "start_date": "2023-01-01",
                        "end_date": None,
                        "duration_months": 12 * i,
                        "is_current": True,
                        "industry": "Software",
                        "company_size": "51-200",
                        "description": f"Built systems for {i} years.",
                    }
                ],
                "education": [
                    {
                        "institution": "IIT Delhi",
                        "degree": "B.Tech",
                        "field_of_study": "Computer Science",
                        "start_year": 2015,
                        "end_year": 2019,
                        "grade": "9.0 CGPA",
                        "tier": "tier_1",
                    }
                ],
                "skills": [
                    {"name": "Python", "proficiency": "advanced", "endorsements": 10},
                    {"name": "Machine Learning", "proficiency": "intermediate", "endorsements": 5},
                ],
                "certifications": [],
                "languages": [
                    {"language": "English", "proficiency": "professional"},
                ],
                "redrob_signals": {
                    "profile_completeness_score": 80.0,
                    "signup_date": "2025-01-01",
                    "last_active_date": "2026-01-01",
                    "open_to_work_flag": True,
                    "profile_views_received_30d": 10,
                    "applications_submitted_30d": 2,
                    "recruiter_response_rate": 0.5,
                    "avg_response_time_hours": 24.0,
                    "skill_assessment_scores": {"Python": 85.0},
                    "connection_count": 100,
                    "endorsements_received": 15,
                    "notice_period_days": 30,
                    "expected_salary_range_inr_lpa": {"min": 10.0, "max": 20.0},
                    "preferred_work_mode": "hybrid",
                    "willing_to_relocate": True,
                    "github_activity_score": 50.0,
                    "search_appearance_30d": 20,
                    "saved_by_recruiters_30d": 3,
                    "interview_completion_rate": 0.9,
                    "offer_acceptance_rate": 0.8,
                    "verified_email": True,
                    "verified_phone": True,
                    "linkedin_connected": True,
                },
            }
            fh.write(json.dumps(candidate) + "\n")

    return jsonl_path


class TestPipelineIntegration:
    """Integration tests for the full pipeline."""

    def test_pipeline_single_candidate(self) -> None:
        """Pipeline should work with a single candidate."""
        jsonl_path = _create_test_jsonl(1)
        output_dir = Path(tempfile.mkdtemp(prefix="output_"))

        result = run_pipeline(
            input_path=jsonl_path,
            output_path=output_dir,
            batch_size=1,
        )

        assert result["total_candidates"] == 1
        assert result["embeddings_shape"] == (1, 384)
        assert (output_dir / "embeddings.npy").exists()
        assert (output_dir / "candidate_ids.npy").exists()
        assert (output_dir / "metadata.json").exists()

    def test_pipeline_batch_candidates(self) -> None:
        """Pipeline should handle a batch of candidates."""
        jsonl_path = _create_test_jsonl(10)
        output_dir = Path(tempfile.mkdtemp(prefix="output_"))

        result = run_pipeline(
            input_path=jsonl_path,
            output_path=output_dir,
            batch_size=4,
        )

        assert result["total_candidates"] == 10
        assert result["embeddings_shape"] == (10, 384)

    def test_output_embeddings_shape(self) -> None:
        """Output embeddings should have correct shape."""
        jsonl_path = _create_test_jsonl(5)
        output_dir = Path(tempfile.mkdtemp(prefix="output_"))

        run_pipeline(input_path=jsonl_path, output_path=output_dir)

        embeddings = np.load(output_dir / "embeddings.npy")
        assert embeddings.shape == (5, 384)
        assert embeddings.dtype == np.float32

    def test_output_embeddings_normalized(self) -> None:
        """Output embeddings should be L2 normalized."""
        jsonl_path = _create_test_jsonl(5)
        output_dir = Path(tempfile.mkdtemp(prefix="output_"))

        run_pipeline(input_path=jsonl_path, output_path=output_dir)

        embeddings = np.load(output_dir / "embeddings.npy")
        norms = np.linalg.norm(embeddings, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-5)

    def test_candidate_id_alignment(self) -> None:
        """Candidate IDs should align with embeddings."""
        num = 5
        jsonl_path = _create_test_jsonl(num)
        output_dir = Path(tempfile.mkdtemp(prefix="output_"))

        run_pipeline(input_path=jsonl_path, output_path=output_dir)

        candidate_ids = np.load(output_dir / "candidate_ids.npy")
        embeddings = np.load(output_dir / "embeddings.npy")

        assert len(candidate_ids) == embeddings.shape[0]
        expected_ids = [f"CAND_{i:07d}" for i in range(1, num + 1)]
        assert list(candidate_ids) == expected_ids

    def test_metadata_content(self) -> None:
        """Metadata file should have correct content."""
        jsonl_path = _create_test_jsonl(3)
        output_dir = Path(tempfile.mkdtemp(prefix="output_"))

        run_pipeline(input_path=jsonl_path, output_path=output_dir)

        with open(output_dir / "metadata.json") as fh:
            metadata = json.load(fh)

        assert metadata["model"] == "BAAI/bge-small-en-v1.5"
        assert metadata["dimension"] == 384
        assert metadata["normalized"] is True
        assert metadata["records_processed"] == 3
        assert "device" in metadata
        assert "timestamp" in metadata

    def test_pipeline_returns_elapsed_time(self) -> None:
        """Pipeline result should include elapsed time."""
        jsonl_path = _create_test_jsonl(2)
        output_dir = Path(tempfile.mkdtemp(prefix="output_"))

        result = run_pipeline(input_path=jsonl_path, output_path=output_dir)

        assert "elapsed_seconds" in result
        assert result["elapsed_seconds"] >= 0

    def test_pipeline_returns_device(self) -> None:
        """Pipeline result should include device info."""
        jsonl_path = _create_test_jsonl(2)
        output_dir = Path(tempfile.mkdtemp(prefix="output_"))

        result = run_pipeline(input_path=jsonl_path, output_path=output_dir, device="cpu")

        assert result["device"] == "cpu"

    def test_pipeline_nonexistent_input(self) -> None:
        """Should raise FileNotFoundError for missing input file."""
        with pytest.raises(FileNotFoundError):
            run_pipeline(
                input_path=Path("/nonexistent/path/data.jsonl"),
                output_path=Path(tempfile.mkdtemp()),
            )

    def test_pipeline_checkpoints_cleaned_on_success(self) -> None:
        """Checkpoints directory should be cleaned after successful run."""
        jsonl_path = _create_test_jsonl(5)
        output_dir = Path(tempfile.mkdtemp(prefix="output_"))

        run_pipeline(input_path=jsonl_path, output_path=output_dir, batch_size=2)

        checkpoint_dir = output_dir / "checkpoints"
        # Checkpoints should be cleaned up after success.
        if checkpoint_dir.exists():
            remaining = list(checkpoint_dir.iterdir())
            assert len(remaining) == 0
