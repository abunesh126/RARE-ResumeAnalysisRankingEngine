"""Text building, embedding generation, and normalization.

Merges the following original modules into a single file:
- formatter/text_builder.py    — candidate_to_text + section builders
- embedding/embedder.py        — generate_embeddings + model cache
- embedding/normalizer.py      — l2_normalize + validate_embeddings
"""

import logging
from collections.abc import Iterator

import numpy as np
from fastembed import TextEmbedding

from resume_embedding.app.config import DEFAULT_SETTINGS
from resume_embedding.app.io import CandidateProfile

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# Text Builder (from formatter/text_builder.py)
# ══════════════════════════════════════════════════════════════════


def _build_current_title_section(profile: CandidateProfile) -> str:
    """Build the [CURRENT_TITLE] section."""
    title = profile.profile.current_title.strip()
    if not title:
        return ""
    return f"[CURRENT_TITLE]\n{title}"


def _build_headline_section(profile: CandidateProfile) -> str:
    """Build the [HEADLINE] section."""
    headline = profile.profile.headline.strip()
    if not headline:
        return ""
    return f"[HEADLINE]\n{headline}"


def _build_summary_section(profile: CandidateProfile) -> str:
    """Build the [SUMMARY] section."""
    summary = profile.profile.summary.strip()
    if not summary:
        return ""
    return f"[SUMMARY]\n{summary}"


def _build_skills_section(profile: CandidateProfile) -> str:
    """Build the [SKILLS] section.

    Format: skill_name (proficiency) separated by ' | '.
    Only includes skills with non-empty names.
    """
    if not profile.skills:
        return ""

    skill_parts: list[str] = []
    for skill in profile.skills:
        name = skill.name.strip()
        if not name:
            continue
        proficiency = skill.proficiency.strip()
        if proficiency:
            skill_parts.append(f"{name} ({proficiency})")
        else:
            skill_parts.append(name)

    if not skill_parts:
        return ""

    return f"[SKILLS]\n{' | '.join(skill_parts)}"


def _build_experience_section(profile: CandidateProfile) -> str:
    """Build the [EXPERIENCE] section.

    Each role includes: title at company (industry, size) - duration
    followed by the role description.
    """
    if not profile.career_history:
        return ""

    entries: list[str] = []
    for role in profile.career_history:
        title = role.title.strip()
        company = role.company.strip()
        if not title and not company:
            continue

        header_parts: list[str] = []
        if title and company:
            header_parts.append(f"{title} at {company}")
        elif title:
            header_parts.append(title)
        else:
            header_parts.append(company)

        context_parts: list[str] = []
        industry = role.industry.strip()
        if industry:
            context_parts.append(industry)
        company_size = role.company_size.strip()
        if company_size:
            context_parts.append(company_size)

        header = header_parts[0]
        if context_parts:
            header += f" ({', '.join(context_parts)})"
        if role.duration_months > 0:
            header += f" - {role.duration_months} months"

        description = role.description.strip()
        if description:
            entries.append(f"{header}\n{description}")
        else:
            entries.append(header)

    if not entries:
        return ""

    return "[EXPERIENCE]\n" + "\n\n".join(entries)


def _build_education_section(profile: CandidateProfile) -> str:
    """Build the [EDUCATION] section.

    Format: degree in field from institution (start_year-end_year)
    """
    if not profile.education:
        return ""

    entries: list[str] = []
    for edu in profile.education:
        institution = edu.institution.strip()
        degree = edu.degree.strip()
        field = edu.field_of_study.strip()

        if not institution and not degree:
            continue

        parts: list[str] = []
        if degree and field:
            parts.append(f"{degree} in {field}")
        elif degree:
            parts.append(degree)
        elif field:
            parts.append(field)

        if institution:
            parts.append(f"from {institution}")

        if edu.start_year > 0 and edu.end_year > 0:
            parts.append(f"({edu.start_year}-{edu.end_year})")
        elif edu.end_year > 0:
            parts.append(f"({edu.end_year})")

        grade = edu.grade.strip() if edu.grade else ""
        if grade:
            parts.append(f"- {grade}")

        entries.append(" ".join(parts))

    if not entries:
        return ""

    return "[EDUCATION]\n" + "\n".join(entries)


def _build_certifications_section(profile: CandidateProfile) -> str:
    """Build the [CERTIFICATIONS] section."""
    if not profile.certifications:
        return ""

    entries: list[str] = []
    for cert in profile.certifications:
        name = cert.name.strip()
        if not name:
            continue
        issuer = cert.issuer.strip()
        year = cert.year

        parts = [name]
        if issuer:
            parts.append(f"({issuer}")
            if year > 0:
                parts[-1] += f", {year})"
            else:
                parts[-1] += ")"
        elif year > 0:
            parts.append(f"({year})")

        entries.append(" ".join(parts))

    if not entries:
        return ""

    return "[CERTIFICATIONS]\n" + "\n".join(entries)


def _build_languages_section(profile: CandidateProfile) -> str:
    """Build the [LANGUAGES] section."""
    if not profile.languages:
        return ""

    lang_parts: list[str] = []
    for lang in profile.languages:
        language = lang.language.strip()
        if not language:
            continue
        proficiency = lang.proficiency.strip()
        if proficiency:
            lang_parts.append(f"{language} ({proficiency})")
        else:
            lang_parts.append(language)

    if not lang_parts:
        return ""

    return f"[LANGUAGES]\n{' | '.join(lang_parts)}"


def _build_metadata_section(profile: CandidateProfile) -> str:
    """Build the [METADATA] section.

    Includes location, country, industry, and years of experience.
    """
    parts: list[str] = []

    location = profile.profile.location.strip()
    country = profile.profile.country.strip()
    if location and country:
        parts.append(f"Location: {location}, {country}")
    elif location:
        parts.append(f"Location: {location}")
    elif country:
        parts.append(f"Location: {country}")

    industry = profile.profile.current_industry.strip()
    if industry:
        parts.append(f"Industry: {industry}")

    yoe = profile.profile.years_of_experience
    if yoe > 0:
        parts.append(f"Experience: {yoe} years")

    company = profile.profile.current_company.strip()
    if company:
        parts.append(f"Company: {company}")

    if not parts:
        return ""

    return "[METADATA]\n" + " | ".join(parts)


# Ordered list of section builders. The ordering is intentional:
# most semantically dense content appears first.
_SECTION_BUILDERS = [
    _build_current_title_section,
    _build_headline_section,
    _build_summary_section,
    _build_skills_section,
    _build_experience_section,
    _build_education_section,
    _build_certifications_section,
    _build_languages_section,
    _build_metadata_section,
]


def candidate_to_text(candidate: CandidateProfile) -> str:
    """Convert a CandidateProfile into structured text for embedding.

    Produces a section-based text representation where sections are ordered
    by semantic importance for retrieval quality. Empty sections are omitted.

    Args:
        candidate: A validated CandidateProfile instance.

    Returns:
        A structured text string suitable for dense embedding generation.
        Sections are separated by double newlines.

    Raises:
        TypeError: If candidate is not a CandidateProfile instance.
    """
    if not isinstance(candidate, CandidateProfile):
        raise TypeError(
            f"Expected CandidateProfile, got {type(candidate).__name__}"
        )

    sections: list[str] = []
    for builder in _SECTION_BUILDERS:
        section = builder(candidate)
        if section:
            sections.append(section)

    return "\n\n".join(sections)


# ══════════════════════════════════════════════════════════════════
# Embedding Generation (from embedding/embedder.py)
# ══════════════════════════════════════════════════════════════════

# Module-level model cache to avoid re-loading the model on every call.
_model_cache: dict[str, TextEmbedding] = {}


def _get_model(model_name: str) -> TextEmbedding:
    """Get or create a cached TextEmbedding model instance.

    Args:
        model_name: HuggingFace model identifier.

    Returns:
        A TextEmbedding instance ready for inference.
    """
    if model_name not in _model_cache:
        logger.info("Loading embedding model: %s", model_name)
        _model_cache[model_name] = TextEmbedding(model_name=model_name)
        logger.info("Model loaded successfully: %s", model_name)
    return _model_cache[model_name]


def generate_embeddings(
    texts: list[str],
    *,
    model_name: str = DEFAULT_SETTINGS.model_name,
    batch_size: int = DEFAULT_SETTINGS.default_batch_size,
    device: str = "cpu",
) -> np.ndarray:
    """Generate dense vector embeddings for a batch of texts.

    Uses FastEmbed's ONNX-based inference. The model is cached after first load.
    The ``device`` parameter is logged for metadata tracking; FastEmbed
    automatically uses CUDAExecutionProvider when ``onnxruntime-gpu`` is installed.

    Args:
        texts: List of text strings to embed.
        model_name: HuggingFace model identifier.
        batch_size: Number of texts to process per inference batch.
        device: Compute device indicator ('cuda' or 'cpu'). Used for logging
            and metadata. FastEmbed handles provider selection internally.

    Returns:
        NumPy array of shape (len(texts), 384) with float32 embeddings.

    Raises:
        ValueError: If texts is empty.
    """
    if not texts:
        raise ValueError("Cannot generate embeddings for an empty text list.")

    model = _get_model(model_name)

    logger.debug("Generating embeddings for %d texts on device=%s", len(texts), device)

    embeddings_iter: Iterator[np.ndarray] = model.embed(
        texts,
        batch_size=batch_size,
    )

    embeddings_list = list(embeddings_iter)
    result = np.array(embeddings_list, dtype=np.float32)

    logger.debug(
        "Generated embeddings: shape=%s, dtype=%s",
        result.shape,
        result.dtype,
    )
    return result


# ══════════════════════════════════════════════════════════════════
# L2 Normalization & Validation (from embedding/normalizer.py)
# ══════════════════════════════════════════════════════════════════


def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    """Normalize each row vector to unit L2 norm.

    Handles zero-norm vectors gracefully by leaving them as zero vectors.

    Args:
        vectors: NumPy array of shape (N, D) with float32 values.

    Returns:
        NumPy array of same shape with each row having L2 norm == 1.0
        (except zero vectors, which remain zero).

    Raises:
        ValueError: If input is not a 2D array.
    """
    if vectors.ndim != 2:
        raise ValueError(
            f"Expected 2D array, got {vectors.ndim}D array with shape {vectors.shape}"
        )

    norms = np.linalg.norm(vectors, axis=1, keepdims=True)

    # Avoid division by zero for zero-norm vectors.
    safe_norms = np.where(norms == 0, 1.0, norms)
    normalized = vectors / safe_norms

    # Ensure float32 output.
    normalized = normalized.astype(np.float32)

    logger.debug(
        "Normalized %d vectors. Min norm: %.6f, Max norm: %.6f",
        vectors.shape[0],
        float(np.min(norms)),
        float(np.max(norms)),
    )
    return normalized


def validate_embeddings(
    vectors: np.ndarray,
    *,
    dimension: int = DEFAULT_SETTINGS.vector_dimension,
    tolerance: float = DEFAULT_SETTINGS.norm_tolerance,
) -> bool:
    """Validate that embeddings meet dimensional and normalization requirements.

    Checks:
    1. Shape is (N, dimension) where dimension defaults to 384.
    2. Data type is float32.
    3. Every row vector has L2 norm within tolerance of 1.0.

    Args:
        vectors: NumPy array to validate.
        dimension: Expected embedding dimensionality (default: 384).
        tolerance: Allowed deviation from unit norm (default: 1e-5).

    Returns:
        True if all validations pass.

    Raises:
        ValueError: If any validation check fails, with a descriptive message.
    """
    # Check dimensionality.
    if vectors.ndim != 2:
        raise ValueError(
            f"Expected 2D array, got {vectors.ndim}D with shape {vectors.shape}"
        )

    if vectors.shape[1] != dimension:
        raise ValueError(
            f"Expected dimension {dimension}, got {vectors.shape[1]}. "
            f"Shape: {vectors.shape}"
        )

    # Check dtype.
    if vectors.dtype != np.float32:
        raise ValueError(
            f"Expected float32, got {vectors.dtype}"
        )

    # Check L2 norms.
    norms = np.linalg.norm(vectors, axis=1)
    non_unit = np.abs(norms - 1.0) > tolerance
    non_unit_count = int(np.sum(non_unit))

    if non_unit_count > 0:
        worst_idx = int(np.argmax(np.abs(norms - 1.0)))
        worst_norm = float(norms[worst_idx])
        raise ValueError(
            f"{non_unit_count} vectors are not L2-normalized (tolerance={tolerance}). "
            f"Worst: index={worst_idx}, norm={worst_norm:.8f}"
        )

    logger.info(
        "Validation passed: %d vectors, dimension=%d, all L2-normalized.",
        vectors.shape[0],
        dimension,
    )
    return True
