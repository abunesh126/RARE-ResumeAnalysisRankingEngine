#!/usr/bin/env python3
"""Benchmark embedding throughput.

Generates synthetic candidate records and measures pipeline throughput
in candidates/second.

Usage:
    python scripts/benchmark.py                    # 100 candidates
    python scripts/benchmark.py --num-candidates 500
    python scripts/benchmark.py --num-candidates 1000 --device cuda
"""

import json
import logging
import sys
import tempfile
from pathlib import Path

from resume_embedding.app.pipeline import run_pipeline


def _generate_synthetic_jsonl(num_candidates: int, output_path: Path) -> Path:
    """Generate a temporary JSONL file with synthetic candidates.

    Args:
        num_candidates: Number of records to generate.
        output_path: Directory to write the file.

    Returns:
        Path to the generated JSONL file.
    """
    jsonl_path = output_path / "benchmark_candidates.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as fh:
        for i in range(1, num_candidates + 1):
            candidate = {
                "candidate_id": f"CAND_{i:07d}",
                "profile": {
                    "anonymized_name": f"Benchmark User {i}",
                    "headline": f"Software Engineer #{i} | Python, Java, Cloud",
                    "summary": (
                        f"Experienced software engineer with {(i % 15) + 1} years "
                        "building distributed systems, microservices, and data pipelines. "
                        "Strong background in agile methodologies and cloud-native architecture."
                    ),
                    "location": ["Bangalore", "Mumbai", "Delhi", "Hyderabad", "Pune"][i % 5],
                    "country": "India",
                    "years_of_experience": float((i % 15) + 1),
                    "current_title": ["Software Engineer", "Senior Developer", "Tech Lead",
                                      "Data Engineer", "ML Engineer"][i % 5],
                    "current_company": f"Company_{i % 50}",
                    "current_company_size": ["51-200", "201-500", "501-1000",
                                              "1001-5000", "5001-10000", "10001+"][i % 6],
                    "current_industry": ["IT Services", "Fintech", "E-commerce",
                                          "Healthcare", "SaaS"][i % 5],
                },
                "career_history": [
                    {
                        "company": f"Company_{i % 50}",
                        "title": "Software Engineer",
                        "start_date": "2023-01-01",
                        "end_date": None,
                        "duration_months": 12 * ((i % 5) + 1),
                        "is_current": True,
                        "industry": "Software",
                        "company_size": "51-200",
                        "description": (
                            f"Built high-throughput systems handling {i * 1000} requests/sec. "
                            "Led migration from monolith to microservices architecture."
                        ),
                    }
                ],
                "education": [
                    {
                        "institution": ["IIT Delhi", "IIT Bombay", "NIT Trichy",
                                         "BITS Pilani", "VIT Vellore"][i % 5],
                        "degree": "B.Tech",
                        "field_of_study": "Computer Science",
                        "start_year": 2015,
                        "end_year": 2019,
                        "grade": f"{7.5 + (i % 20) / 10:.1f} CGPA",
                        "tier": ["tier_1", "tier_1", "tier_1", "tier_1", "tier_2"][i % 5],
                    }
                ],
                "skills": [
                    {"name": "Python", "proficiency": "advanced", "endorsements": 10 + i % 50},
                    {"name": "Java", "proficiency": "intermediate", "endorsements": 5 + i % 30},
                    {"name": "AWS", "proficiency": "intermediate", "endorsements": 3 + i % 20},
                ],
                "certifications": [],
                "languages": [
                    {"language": "English", "proficiency": "professional"},
                ],
                "redrob_signals": {
                    "profile_completeness_score": 70.0 + (i % 30),
                    "signup_date": "2025-01-01",
                    "last_active_date": "2026-01-01",
                    "open_to_work_flag": i % 2 == 0,
                    "profile_views_received_30d": 10 + i % 100,
                    "applications_submitted_30d": i % 10,
                    "recruiter_response_rate": 0.3 + (i % 7) / 10,
                    "avg_response_time_hours": 12.0 + (i % 48),
                    "skill_assessment_scores": {"Python": 60.0 + i % 40},
                    "connection_count": 50 + i * 3,
                    "endorsements_received": 10 + i % 50,
                    "notice_period_days": [30, 60, 90][i % 3],
                    "expected_salary_range_inr_lpa": {
                        "min": 8.0 + (i % 20),
                        "max": 15.0 + (i % 30),
                    },
                    "preferred_work_mode": ["remote", "hybrid", "onsite"][i % 3],
                    "willing_to_relocate": i % 3 == 0,
                    "github_activity_score": 10.0 + (i % 80),
                    "search_appearance_30d": 20 + i % 200,
                    "saved_by_recruiters_30d": i % 15,
                    "interview_completion_rate": 0.5 + (i % 5) / 10,
                    "offer_acceptance_rate": 0.4 + (i % 6) / 10,
                    "verified_email": True,
                    "verified_phone": i % 2 == 0,
                    "linkedin_connected": i % 3 == 0,
                },
            }
            fh.write(json.dumps(candidate) + "\n")

    return jsonl_path


def main() -> None:
    """Run the benchmark."""
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark embedding throughput.")
    parser.add_argument("--num-candidates", type=int, default=100,
                        help="Number of synthetic candidates to generate (default: 100).")
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"])
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    tmp_dir = Path(tempfile.mkdtemp(prefix="benchmark_"))
    output_dir = tmp_dir / "outputs"

    print(f"\n{'='*60}")
    print(f"BENCHMARK — {args.num_candidates} synthetic candidates")
    print(f"Batch size: {args.batch_size}")
    print(f"Device:     {args.device}")
    print(f"{'='*60}\n")

    print("Generating synthetic dataset...")
    jsonl_path = _generate_synthetic_jsonl(args.num_candidates, tmp_dir)
    print(f"Generated: {jsonl_path}\n")

    result = run_pipeline(
        input_path=jsonl_path,
        output_path=output_dir,
        batch_size=args.batch_size,
        device=args.device,
    )

    throughput = result["total_candidates"] / result["elapsed_seconds"] if result["elapsed_seconds"] > 0 else 0

    print(f"\n{'='*60}")
    print("BENCHMARK RESULTS")
    print(f"{'='*60}")
    print(f"  Candidates:  {result['total_candidates']}")
    print(f"  Embeddings:  {result['embeddings_shape']}")
    print(f"  Device:      {result['device']}")
    print(f"  Elapsed:     {result['elapsed_seconds']:.2f} seconds")
    print(f"  Throughput:  {throughput:.1f} candidates/sec")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
