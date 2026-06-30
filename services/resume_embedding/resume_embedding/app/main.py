"""CLI entry point for the resume embedding pipeline.

Usage:
    python -m resume_embedding.main --input data/sample/sample_candidates.jsonl
    python -m resume_embedding.main --input resume.pdf
    python -m resume_embedding.main --input resume.png
    python -m resume_embedding.main --input resume.md
    python -m resume_embedding.main --input resume.txt
    python -m resume_embedding.main --input data.jsonl --output data/output/ --device cuda
    python -m resume_embedding.main --resume --output data/output/
    resume-embed --input data.jsonl --device cuda --verbose
"""

import argparse
import logging
import sys
from pathlib import Path

from resume_embedding.app.config import DEFAULT_SETTINGS, PipelineSettings
from resume_embedding.app.pipeline import run_pipeline


def _configure_logging(verbose: bool = False) -> None:
    """Configure structured logging for the pipeline.

    Args:
        verbose: If True, set log level to DEBUG. Otherwise INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="resume-embed",
        description="Generate dense vector embeddings for candidate profiles.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # Structured candidates (JSONL / JSON)\n"
            "  resume-embed --input data/sample/sample_candidates.jsonl\n"
            "  resume-embed --input candidates.json --device cuda\n\n"
            "  # PDF resume\n"
            "  resume-embed --input resume.pdf --output outputs/pdf_run/\n\n"
            "  # Image resume (OCR)\n"
            "  resume-embed --input resume.png\n"
            "  resume-embed --input scan.tiff\n\n"
            "  # Markdown / plain text resume\n"
            "  resume-embed --input resume.md\n"
            "  resume-embed --input resume.txt\n\n"
            "  # Advanced\n"
            "  resume-embed --input data.jsonl --output data/output/ --device cuda\n"
            "  resume-embed --resume --output data/output/\n"
            "  python -m resume_embedding.main --input data.jsonl --batch-size 512 --verbose\n"
        ),
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help=(
            "Path to the input file. Supported formats: "
            ".jsonl (streamed structured records), "
            ".json (structured records array), "
            ".pdf (PDF resume — requires PyMuPDF), "
            ".png/.jpg/.jpeg/.bmp/.tiff (image OCR — requires pytesseract + Pillow), "
            ".md (markdown resume), "
            ".txt (plain text resume). "
            "Required unless --resume is specified."
        ),
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Directory for output artifacts (default: auto-generated data/output/run_<timestamp>/).",
    )
    parser.add_argument(
        "--device",
        type=str,
        choices=["auto", "cuda", "cpu"],
        default=None,
        help="Compute device: auto (detect), cuda, or cpu (default: auto).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Embedding batch size (default: 256).",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=False,
        help="Resume from the last checkpoint in --output directory.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to a YAML config file to override defaults.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Enable debug logging.",
    )
    return parser


def main() -> None:
    """Main entry point for the CLI.

    Parses arguments, loads configuration, and runs the embedding pipeline.
    Exits with code 0 on success, 1 on error.
    """
    parser = _build_parser()
    args = parser.parse_args()

    _configure_logging(verbose=args.verbose)

    logger = logging.getLogger(__name__)

    # Validate: either --input or --resume must be provided.
    if not args.input and not args.resume:
        parser.error("--input is required unless --resume is specified.")

    try:
        # Build settings: YAML config (if provided) → CLI overrides.
        if args.config:
            settings = PipelineSettings.from_yaml(
                Path(args.config),
                default_batch_size=args.batch_size,
                device=args.device,
            )
        else:
            overrides = {}
            if args.batch_size is not None:
                overrides["default_batch_size"] = args.batch_size
            if args.device is not None:
                overrides["device"] = args.device

            if overrides:
                settings = PipelineSettings(**{
                    **DEFAULT_SETTINGS.model_dump(),
                    **overrides,
                })
            else:
                settings = DEFAULT_SETTINGS

        # For --resume without --input, pass a placeholder; the pipeline
        # will read the actual input path from the checkpoint state.
        input_path = args.input if args.input else "."

        result = run_pipeline(
            input_path=input_path,
            output_path=args.output,
            batch_size=args.batch_size,
            device=args.device,
            resume=args.resume,
            settings=settings,
        )

        logger.info(
            "Pipeline finished successfully. "
            "Processed %d candidates in %.1f seconds.",
            result["total_candidates"],
            result["elapsed_seconds"],
        )

    except FileNotFoundError as exc:
        logger.error("File not found: %s", exc)
        sys.exit(1)
    except ValueError as exc:
        logger.error("Validation error: %s", exc)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user.")
        sys.exit(130)
    except Exception as exc:
        logger.exception("Unexpected error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
