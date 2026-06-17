"""Structured text builder for candidate profiles.

Converts a CandidateProfile into a section-based text representation
optimized for dense embedding with BAAI/bge-small-en-v1.5.

Section ordering prioritizes the most semantically dense fields first,
since transformer models attend most heavily to early tokens.
"""

from resume_embedding.parser.candidate_parser import CandidateProfile


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
