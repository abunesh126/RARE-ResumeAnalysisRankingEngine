"""Backward-compatible entry point.

Allows `python -m resume_embedding.main` to keep working.
"""

from resume_embedding.app.main import main

if __name__ == "__main__":
    main()
