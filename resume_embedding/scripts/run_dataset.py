#!/usr/bin/env python3
"""Full dataset processing with CLI arguments.

Usage:
    python scripts/run_dataset.py --input datasets/input/candidates.jsonl
    python scripts/run_dataset.py --input data.jsonl --output outputs/run1 --device cuda
    python scripts/run_dataset.py --resume --output outputs/run1
"""

import sys
from pathlib import Path

# Ensure the project root is on sys.path when run as a script.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from resume_embedding.main import main

if __name__ == "__main__":
    main()
