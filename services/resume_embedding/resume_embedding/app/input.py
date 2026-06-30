"""Input module for the resume embedding pipeline.

Consolidates all format-specific readers, the unified dispatcher,
and the resume text normalizer into a single module.

Replaces the following previous subpackages:
  - app/input/dispatcher.py
  - app/input/jsonl_reader.py
  - app/input/json_reader.py
  - app/input/pdf_reader.py
  - app/input/image_reader.py
  - app/input/markdown_reader.py
  - app/input/text_reader.py
  - app/normalizer/resume_normalizer.py

Public API (unchanged):
  dispatch(path, *, skip_invalid=True)  -> Iterator[(candidate_id, text)]
  detect_input_type(path)               -> str
  normalize_resume_text(raw_text)       -> str
  SUPPORTED_EXTENSIONS                  -> frozenset[str]

To add a new format:
  1. Add its extension(s) to the appropriate frozenset constant below.
  2. Write a ``_load_<format>(path) -> Iterator[tuple[str, str]]`` function.
  3. Add a branch in ``dispatch()``.
  Nothing else needs to change.
"""

import logging
import re
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

from resume_embedding.app.io import _load_json_array, _load_jsonl
from resume_embedding.app.model import candidate_to_text

if TYPE_CHECKING:
    from PIL import Image

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# Resume Text Normalizer
# (previously: app/normalizer/resume_normalizer.py)
# ══════════════════════════════════════════════════════════════════

# Patterns compiled once at module load for efficiency.
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MULTIPLE_SPACES = re.compile(r"[ \t]+")
_MULTIPLE_NEWLINES = re.compile(r"\n{3,}")
_SEPARATOR_LINES = re.compile(r"^[-=_*]{3,}\s*$", re.MULTILINE)
_LEADING_TRAILING_WHITESPACE_PER_LINE = re.compile(r"^[ \t]+|[ \t]+$", re.MULTILINE)


def normalize_resume_text(raw_text: str) -> str:
    """Clean and normalize raw resume text from any unstructured source.

    Applies the following transformations in order:
    1. Remove null bytes and control characters.
    2. Normalize line endings to ``\\n``.
    3. Strip per-line leading/trailing whitespace.
    4. Collapse multiple consecutive spaces/tabs into a single space.
    5. Remove separator-only lines (``---``, ``===``, ``***``, etc.).
    6. Collapse 3+ consecutive blank lines into exactly two.
    7. Strip the entire string.

    Args:
        raw_text: Raw text as returned by a format extractor.

    Returns:
        Cleaned text string. Returns an empty string if the input is
        empty or whitespace-only after normalization.

    Raises:
        TypeError: If raw_text is not a string.
    """
    if not isinstance(raw_text, str):
        raise TypeError(f"Expected str, got {type(raw_text).__name__}")

    if not raw_text.strip():
        logger.debug("normalize_resume_text: received empty or whitespace-only text.")
        return ""

    text = raw_text

    # Step 1: Remove control characters (keep \n, \r, \t).
    text = _CONTROL_CHARS.sub("", text)

    # Step 2: Normalize Windows/Mac line endings to Unix newlines.
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Step 3: Strip leading/trailing whitespace per line.
    text = _LEADING_TRAILING_WHITESPACE_PER_LINE.sub("", text)

    # Step 4: Collapse multiple spaces/tabs within a line.
    text = _MULTIPLE_SPACES.sub(" ", text)

    # Step 5: Remove separator-only lines (---, ===, ***, ___).
    text = _SEPARATOR_LINES.sub("", text)

    # Step 6: Collapse 3+ consecutive blank lines into two (one blank line).
    text = _MULTIPLE_NEWLINES.sub("\n\n", text)

    # Step 7: Strip the whole string.
    text = text.strip()

    logger.debug(
        "normalize_resume_text: %d chars in → %d chars out.",
        len(raw_text),
        len(text),
    )
    return text


# ══════════════════════════════════════════════════════════════════
# Shared helpers
# ══════════════════════════════════════════════════════════════════


def _make_file_id(path: Path) -> str:
    """Derive a stable candidate ID from a file's stem.

    Args:
        path: Path to the input file.

    Returns:
        A string of the form ``FILE_<stem>`` where ``<stem>`` is the
        filename without extension, with spaces replaced by underscores.
    """
    stem = path.stem.replace(" ", "_")
    return f"FILE_{stem}"


# ══════════════════════════════════════════════════════════════════
# Format-Specific Readers
# ══════════════════════════════════════════════════════════════════


def _load_jsonl_records(
    path: Path,
    *,
    skip_invalid: bool = True,
) -> Iterator[tuple[str, str]]:
    """Stream ``(candidate_id, text)`` tuples from a JSONL file.

    Each line is validated against the CandidateProfile Pydantic schema.
    Invalid records are logged and skipped when ``skip_invalid`` is True.

    Args:
        path: Path to the ``.jsonl`` file.
        skip_invalid: If True, skip records that fail validation.

    Yields:
        ``(candidate_id, normalized_text)`` tuples.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If skip_invalid is False and a record fails validation.
    """
    logger.info("JSONL reader: %s", path)
    for candidate in _load_jsonl(path, skip_invalid=skip_invalid):
        yield candidate.candidate_id, candidate_to_text(candidate)


def _load_json_records(
    path: Path,
    *,
    skip_invalid: bool = True,
) -> Iterator[tuple[str, str]]:
    """Yield ``(candidate_id, text)`` tuples from a JSON array file.

    The file must contain a top-level JSON array of candidate objects,
    each validated against the CandidateProfile Pydantic schema.

    Args:
        path: Path to the ``.json`` file.
        skip_invalid: If True, skip records that fail validation.

    Yields:
        ``(candidate_id, normalized_text)`` tuples.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a JSON array, or if skip_invalid is
            False and a record fails validation.
    """
    logger.info("JSON reader: %s", path)
    for candidate in _load_json_array(path, skip_invalid=skip_invalid):
        yield candidate.candidate_id, candidate_to_text(candidate)


def _load_pdf(path: Path) -> Iterator[tuple[str, str]]:
    """Yield a single ``(candidate_id, text)`` tuple from a PDF resume.

    Reads every page of the PDF in order, concatenates the extracted text,
    and applies the resume text normalizer before yielding.

    Requires the ``pymupdf`` package (``pip install "resume-embedding[pdf]"``).

    Args:
        path: Path to the ``.pdf`` file.

    Yields:
        A single ``(candidate_id, normalized_text)`` tuple.

    Raises:
        ImportError: If ``pymupdf`` is not installed.
        FileNotFoundError: If the PDF file does not exist.
        RuntimeError: If PyMuPDF cannot open or read the file.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise ImportError(
            "PDF extraction requires PyMuPDF. "
            "Install it with: pip install pymupdf"
        ) from exc

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    logger.info("PDF reader: %s", path)

    try:
        doc = fitz.open(str(path))
    except Exception as exc:
        raise RuntimeError(f"Could not open PDF '{path}': {exc}") from exc

    page_texts: list[str] = []
    try:
        for page_num, page in enumerate(doc, start=1):
            page_text = page.get_text("text")  # type: ignore[attr-defined]
            if page_text.strip():
                page_texts.append(page_text)
                logger.debug("PDF page %d: %d chars extracted.", page_num, len(page_text))
            else:
                logger.debug("PDF page %d: empty, skipping.", page_num)
    finally:
        doc.close()

    raw_text = "\n\n".join(page_texts)
    normalized = normalize_resume_text(raw_text)

    if not normalized:
        logger.warning("PDF reader: no text extracted from %s (scanned or encrypted?)", path.name)

    candidate_id = _make_file_id(path)
    logger.info(
        "PDF reader: extracted %d chars from %s → candidate_id=%s",
        len(normalized),
        path.name,
        candidate_id,
    )
    yield candidate_id, normalized


# ── Markdown stripping patterns (compiled once) ───────────────────

_MD_HEADING = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
_MD_BOLD = re.compile(r"\*{2}(.+?)\*{2}|_{2}(.+?)_{2}")
_MD_ITALIC = re.compile(r"\*(.+?)\*|_(.+?)_")
_MD_INLINE_CODE = re.compile(r"`(.+?)`")
_MD_CODE_BLOCK = re.compile(r"```[\s\S]*?```|~~~[\s\S]*?~~~")
_MD_STRIKETHROUGH = re.compile(r"~~(.+?)~~")
_MD_HR = re.compile(r"^(\s*[-*_]){3,}\s*$", re.MULTILINE)
_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_MD_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
_MD_LIST_MARKER = re.compile(r"^\s*[-*+]\s+", re.MULTILINE)
_MD_ORDERED_LIST = re.compile(r"^\s*\d+\.\s+", re.MULTILINE)
_MD_BLOCKQUOTE = re.compile(r"^\s*>\s?", re.MULTILINE)
_MD_HTML_TAG = re.compile(r"<[^>]+>")


def _strip_markdown(text: str) -> str:
    """Remove markdown syntax tokens while preserving readable content.

    Transforms markdown-formatted text into clean prose suitable for
    embedding. Preserves section hierarchy by keeping heading text.

    Args:
        text: Raw markdown string.

    Returns:
        Plain text with markdown tokens removed.
    """
    # Remove fenced code blocks entirely (code is low-signal for resume matching).
    text = _MD_CODE_BLOCK.sub("", text)
    # Remove images entirely.
    text = _MD_IMAGE.sub("", text)
    # Unwrap links: keep the display text, drop the URL.
    text = _MD_LINK.sub(r"\1", text)
    # Unwrap headings: keep the heading text.
    text = _MD_HEADING.sub(r"\1", text)
    # Remove horizontal rules.
    text = _MD_HR.sub("", text)
    # Remove blockquote markers.
    text = _MD_BLOCKQUOTE.sub("", text)
    # Remove list markers.
    text = _MD_LIST_MARKER.sub("", text)
    text = _MD_ORDERED_LIST.sub("", text)
    # Unwrap bold, italic, inline code, strikethrough — keep the inner text.
    text = _MD_BOLD.sub(lambda m: m.group(1) or m.group(2), text)
    text = _MD_ITALIC.sub(lambda m: m.group(1) or m.group(2), text)
    text = _MD_INLINE_CODE.sub(r"\1", text)
    text = _MD_STRIKETHROUGH.sub(r"\1", text)
    # Strip HTML tags.
    text = _MD_HTML_TAG.sub("", text)
    return text


def _load_markdown(path: Path) -> Iterator[tuple[str, str]]:
    """Yield a single ``(candidate_id, text)`` tuple from a markdown resume.

    Reads the file as UTF-8, strips markdown syntax, and normalizes the
    resulting text before yielding.

    Args:
        path: Path to the ``.md`` file.

    Yields:
        A single ``(candidate_id, normalized_text)`` tuple.

    Raises:
        FileNotFoundError: If the markdown file does not exist.
        UnicodeDecodeError: If the file cannot be decoded as UTF-8.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Markdown file not found: {path}")

    logger.info("Markdown reader: %s", path)

    raw = path.read_text(encoding="utf-8")
    stripped = _strip_markdown(raw)
    normalized = normalize_resume_text(stripped)

    if not normalized:
        logger.warning("Markdown reader: no text extracted from %s", path.name)

    candidate_id = _make_file_id(path)
    logger.info(
        "Markdown reader: extracted %d chars from %s → candidate_id=%s",
        len(normalized),
        path.name,
        candidate_id,
    )
    yield candidate_id, normalized


def _load_text(path: Path) -> Iterator[tuple[str, str]]:
    """Yield a single ``(candidate_id, text)`` tuple from a plain text resume.

    Reads the file as UTF-8 and applies the resume text normalizer to
    collapse whitespace and remove control characters.

    Args:
        path: Path to the ``.txt`` file.

    Yields:
        A single ``(candidate_id, normalized_text)`` tuple.

    Raises:
        FileNotFoundError: If the text file does not exist.
        UnicodeDecodeError: If the file cannot be decoded as UTF-8.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Text file not found: {path}")

    logger.info("Text reader: %s", path)

    raw = path.read_text(encoding="utf-8")
    normalized = normalize_resume_text(raw)

    if not normalized:
        logger.warning("Text reader: empty file %s", path.name)

    candidate_id = _make_file_id(path)
    logger.info(
        "Text reader: extracted %d chars from %s → candidate_id=%s",
        len(normalized),
        path.name,
        candidate_id,
    )
    yield candidate_id, normalized


#: Tesseract page segmentation mode: assume a single uniform block of text.
_PSM_SINGLE_BLOCK = "--psm 6"


def _preprocess_image(image: "Image.Image") -> "Image.Image":  # type: ignore[name-defined]
    """Apply basic preprocessing to improve OCR accuracy.

    Steps:
        1. Convert to grayscale (removes color noise).
        2. Sharpen to help with blurry scans.
        3. Auto-contrast to normalize brightness range.

    Args:
        image: A Pillow Image object.

    Returns:
        A preprocessed Pillow Image object in mode ``'L'``.
    """
    from PIL import ImageFilter, ImageOps

    gray = image.convert("L")
    sharpened = gray.filter(ImageFilter.SHARPEN)
    enhanced = ImageOps.autocontrast(sharpened)
    return enhanced


def _load_image(path: Path) -> Iterator[tuple[str, str]]:
    """Yield a single ``(candidate_id, text)`` tuple from a resume image.

    Applies grayscale conversion and auto-contrast before running Tesseract
    OCR, then normalizes the resulting text.

    Requires:
        - ``pytesseract`` package (``pip install pytesseract``)
        - ``Pillow`` package (``pip install Pillow``)
        - Tesseract OCR binary on the system PATH

    Args:
        path: Path to the image file (.png, .jpg, .jpeg, .bmp, .tiff).

    Yields:
        A single ``(candidate_id, normalized_text)`` tuple.

    Raises:
        ImportError: If ``pytesseract`` or ``Pillow`` is not installed.
        FileNotFoundError: If the image file does not exist.
        RuntimeError: If OCR fails (e.g., Tesseract binary not found).
    """
    try:
        import pytesseract
    except ImportError as exc:
        raise ImportError(
            "Image OCR requires pytesseract. "
            "Install it with: pip install pytesseract Pillow\n"
            "Also install the Tesseract binary: "
            "https://github.com/UB-Mannheim/tesseract/wiki"
        ) from exc

    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError(
            "Image OCR requires Pillow. "
            "Install it with: pip install Pillow"
        ) from exc

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")

    logger.info("Image reader (OCR): %s", path)

    try:
        image = Image.open(str(path))
    except Exception as exc:
        raise RuntimeError(f"Could not open image '{path}': {exc}") from exc

    try:
        preprocessed = _preprocess_image(image)
    finally:
        image.close()

    try:
        raw_text: str = pytesseract.image_to_string(
            preprocessed,
            config=_PSM_SINGLE_BLOCK,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Tesseract OCR failed for '{path}': {exc}\n"
            "Ensure the Tesseract binary is installed and on your PATH."
        ) from exc

    normalized = normalize_resume_text(raw_text)

    if not normalized:
        logger.warning("Image reader: no text extracted from %s", path.name)

    candidate_id = _make_file_id(path)
    logger.info(
        "Image reader: extracted %d chars from %s → candidate_id=%s",
        len(normalized),
        path.name,
        candidate_id,
    )
    yield candidate_id, normalized


# ══════════════════════════════════════════════════════════════════
# Format Dispatcher
# (previously: app/input/dispatcher.py)
# ══════════════════════════════════════════════════════════════════

_JSONL_EXT = frozenset({".jsonl"})
_JSON_EXT = frozenset({".json"})
_PDF_EXT = frozenset({".pdf"})
_IMAGE_EXT = frozenset({".png", ".jpg", ".jpeg", ".bmp", ".tiff"})
_MARKDOWN_EXT = frozenset({".md"})
_TEXT_EXT = frozenset({".txt"})

#: All file extensions recognized by the dispatcher.
SUPPORTED_EXTENSIONS: frozenset[str] = (
    _JSONL_EXT | _JSON_EXT | _PDF_EXT | _IMAGE_EXT | _MARKDOWN_EXT | _TEXT_EXT
)


def detect_input_type(path: Path) -> str:
    """Return a human-readable format name for the given file extension.

    Args:
        path: Path to the input file.

    Returns:
        One of ``'jsonl'``, ``'json'``, ``'pdf'``, ``'image'``,
        ``'markdown'``, or ``'text'``.

    Raises:
        ValueError: If the file extension is not supported.
    """
    ext = Path(path).suffix.lower()

    if ext in _JSONL_EXT:
        return "jsonl"
    if ext in _JSON_EXT:
        return "json"
    if ext in _PDF_EXT:
        return "pdf"
    if ext in _IMAGE_EXT:
        return "image"
    if ext in _MARKDOWN_EXT:
        return "markdown"
    if ext in _TEXT_EXT:
        return "text"

    raise ValueError(
        f"Unsupported file extension '{ext}'. "
        f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
    )


def dispatch(
    path: Path,
    *,
    skip_invalid: bool = True,
) -> Iterator[tuple[str, str]]:
    """Route an input file to the correct reader and yield (id, text) tuples.

    This is the single entry point for all format-specific loading.
    The caller never needs to know which format is being processed.

    Args:
        path: Path to the input file (any supported format).
        skip_invalid: Passed to JSONL/JSON readers — if True, invalid
            structured records are logged and skipped rather than raising.

    Yields:
        ``(candidate_id, normalized_text)`` tuples.

        - For ``.jsonl`` / ``.json``: one tuple per valid candidate record.
        - For all other formats: exactly one tuple per file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file extension is unsupported.
        ImportError: If an optional dependency (PyMuPDF, pytesseract,
            Pillow) is required but not installed.
        RuntimeError: If an extractor encounters an unrecoverable error
            (e.g., Tesseract binary missing, corrupt PDF).
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    fmt = detect_input_type(path)
    logger.info("Dispatching '%s' as format: %s", path.name, fmt)

    if fmt == "jsonl":
        yield from _load_jsonl_records(path, skip_invalid=skip_invalid)
    elif fmt == "json":
        yield from _load_json_records(path, skip_invalid=skip_invalid)
    elif fmt == "pdf":
        yield from _load_pdf(path)
    elif fmt == "image":
        yield from _load_image(path)
    elif fmt == "markdown":
        yield from _load_markdown(path)
    elif fmt == "text":
        yield from _load_text(path)
    else:
        # Should never happen — detect_input_type() guards this.
        raise ValueError(f"Internal error: unhandled format '{fmt}'")
