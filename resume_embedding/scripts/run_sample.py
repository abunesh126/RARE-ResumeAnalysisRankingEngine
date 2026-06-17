#!/usr/bin/env python3
"""Quick test with the bundled sample dataset.

Usage:
    python scripts/run_sample.py
    python scripts/run_sample.py --device cuda
    python scripts/run_sample.py --verbose
"""

import sys
from pathlib import Path

# Ensure the project root is on sys.path when run as a script.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from resume_embedding.config.settings import DEFAULT_SETTINGS
from resume_embedding.pipeline.embedding_pipeline import run_pipeline


def main() -> None:
    """Run the embedding pipeline on the sample dataset."""
    import argparse
    import logging

    parser = argparse.ArgumentParser(description="Run sample dataset embedding.")
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

    sample_path = _PROJECT_ROOT / "datasets" / "sample" / "sample_candidates.jsonl"

    if not sample_path.exists():
        print(f"ERROR: Sample dataset not found at {sample_path}")
        sys.exit(1)

    # Output will auto-generate a timestamped folder under outputs/.
    print(f"\n{'='*60}")
    print("SAMPLE RUN — 10 candidates")
    print(f"Input:  {sample_path}")
    print(f"Output: outputs/run_<timestamp>/ (auto-generated)")
    print(f"{'='*60}\n")

    result = run_pipeline(
        input_path=sample_path,
        device=args.device,
    )

    print(f"\n✓ Processed {result['total_candidates']} candidates in {result['elapsed_seconds']}s")
    print(f"  Embeddings: {result['embeddings_shape']}")
    print(f"  Device:     {result['device']}")
    print(f"  Output:     {result['output_dir']}")


if __name__ == "__main__":
    main()
