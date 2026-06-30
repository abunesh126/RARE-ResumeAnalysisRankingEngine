#!/usr/bin/env python3
"""Full dataset processing with CLI arguments.

Usage:
    python scripts/run_dataset.py --input data/input/candidates.jsonl
    python scripts/run_dataset.py --input data.jsonl --output data/output/run1 --device cuda
    python scripts/run_dataset.py --resume --output data/output/run1
"""
from resume_embedding.app.main import main

if __name__ == "__main__":
    main()
