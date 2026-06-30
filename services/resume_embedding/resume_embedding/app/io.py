"""Input loading, validation, output writing, metadata writing, and checkpoint handling.

Merges the following original modules into a single file:
- parser/candidate_parser.py  — Pydantic models + JSONL/JSON reader
- storage/npy_writer.py       — .npy save/load for embeddings
- storage/metadata_writer.py  — metadata.json writer
- pipeline/checkpoint.py      — CheckpointManager for crash recovery
"""

import logging
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import orjson
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# Pydantic Models (from parser/candidate_parser.py)
# ══════════════════════════════════════════════════════════════════


class ProfileInfo(BaseModel):
    """Top-level profile information for a candidate.

    Contains identity, title, summary, location, and current employment details.
    """

    anonymized_name: str = Field(description="Anonymized full name.")
    headline: str = Field(default="", description="One-line professional headline.")
    summary: str = Field(default="", description="Multi-sentence professional summary.")
    location: str = Field(default="", description="City, region/state.")
    country: str = Field(default="", description="Country.")
    years_of_experience: float = Field(default=0.0, ge=0, le=50, description="Total years of experience.")
    current_title: str = Field(default="", description="Current job title.")
    current_company: str = Field(default="", description="Current employer.")
    current_company_size: str = Field(default="", description="Company size bucket.")
    current_industry: str = Field(default="", description="Current industry.")


class CareerEntry(BaseModel):
    """A single career history entry.

    Represents one role in the candidate's work history.
    """

    company: str = Field(description="Company name.")
    title: str = Field(description="Job title.")
    start_date: str = Field(default="", description="Start date (YYYY-MM-DD).")
    end_date: str | None = Field(default=None, description="End date or null if current.")
    duration_months: int = Field(default=0, ge=0, description="Duration in months.")
    is_current: bool = Field(default=False, description="Whether this is the current role.")
    industry: str = Field(default="", description="Industry of the employer.")
    company_size: str = Field(default="", description="Company size bucket.")
    description: str = Field(default="", description="Role responsibilities and achievements.")


class EducationEntry(BaseModel):
    """A single education record.

    Represents one degree or educational program.
    """

    institution: str = Field(description="Institution name.")
    degree: str = Field(default="", description="Degree type (B.Tech, M.Sc, etc.).")
    field_of_study: str = Field(default="", description="Field of study / major.")
    start_year: int = Field(default=0, ge=0, description="Start year.")
    end_year: int = Field(default=0, ge=0, description="End year.")
    grade: str | None = Field(default=None, description="GPA / percentage / class.")
    tier: str | None = Field(default=None, description="Institution prestige tier.")


class SkillEntry(BaseModel):
    """A single skill record.

    Includes proficiency level and endorsement count.
    """

    name: str = Field(description="Skill name.")
    proficiency: str = Field(default="", description="Proficiency level.")
    endorsements: int = Field(default=0, ge=0, description="Number of endorsements.")
    duration_months: int | None = Field(default=None, ge=0, description="Months of experience with this skill.")


class CertificationEntry(BaseModel):
    """A single certification record."""

    name: str = Field(description="Certification name.")
    issuer: str = Field(default="", description="Issuing organization.")
    year: int = Field(default=0, ge=0, description="Year obtained.")


class LanguageEntry(BaseModel):
    """A single language proficiency record."""

    language: str = Field(description="Language name.")
    proficiency: str = Field(default="", description="Proficiency level.")


class SalaryRange(BaseModel):
    """Expected salary range in INR Lakhs Per Annum."""

    min: float = Field(default=0.0, ge=0, description="Minimum expected salary (LPA).")
    max: float = Field(default=0.0, ge=0, description="Maximum expected salary (LPA).")


class RedrobSignals(BaseModel):
    """Platform behavioral and engagement signals.

    These are numeric/boolean metrics from the Redrob ecosystem.
    Excluded from text embedding but preserved for downstream ranking teams.
    """

    profile_completeness_score: float = Field(default=0.0)
    signup_date: str = Field(default="")
    last_active_date: str = Field(default="")
    open_to_work_flag: bool = Field(default=False)
    profile_views_received_30d: int = Field(default=0)
    applications_submitted_30d: int = Field(default=0)
    recruiter_response_rate: float = Field(default=0.0)
    avg_response_time_hours: float = Field(default=0.0)
    skill_assessment_scores: dict[str, float] = Field(default_factory=dict)
    connection_count: int = Field(default=0)
    endorsements_received: int = Field(default=0)
    notice_period_days: int = Field(default=0)
    expected_salary_range_inr_lpa: SalaryRange = Field(default_factory=SalaryRange)
    preferred_work_mode: str = Field(default="")
    willing_to_relocate: bool = Field(default=False)
    github_activity_score: float = Field(default=-1.0)
    search_appearance_30d: int = Field(default=0)
    saved_by_recruiters_30d: int = Field(default=0)
    interview_completion_rate: float = Field(default=0.0)
    offer_acceptance_rate: float = Field(default=-1.0)
    verified_email: bool = Field(default=False)
    verified_phone: bool = Field(default=False)
    linkedin_connected: bool = Field(default=False)


class CandidateProfile(BaseModel):
    """Complete candidate profile as stored in candidates.jsonl.

    This is the top-level model representing one JSONL line.
    All fields use defaults so partial records can still be parsed.
    """

    candidate_id: str = Field(description="Unique identifier (CAND_XXXXXXX).")
    profile: ProfileInfo = Field(default_factory=ProfileInfo)
    career_history: list[CareerEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    skills: list[SkillEntry] = Field(default_factory=list)
    certifications: list[CertificationEntry] = Field(default_factory=list)
    languages: list[LanguageEntry] = Field(default_factory=list)
    redrob_signals: RedrobSignals = Field(default_factory=RedrobSignals)

    @field_validator("candidate_id")
    @classmethod
    def validate_candidate_id(cls, v: str) -> str:
        """Ensure candidate_id matches the expected pattern."""
        if not v.startswith("CAND_"):
            raise ValueError(f"candidate_id must start with 'CAND_', got: {v!r}")
        return v


# ══════════════════════════════════════════════════════════════════
# Candidate Loading (from parser/candidate_parser.py)
# ══════════════════════════════════════════════════════════════════


def load_candidates(
    input_path: Path,
    *,
    skip_invalid: bool = True,
) -> Iterator[CandidateProfile]:
    """Stream candidate profiles from a JSONL or JSON file.

    Auto-detects format by file extension:
    - ``.jsonl`` — one JSON object per line (streaming, memory-efficient)
    - ``.json``  — JSON array of objects (loaded into memory)

    Invalid records are logged and skipped when skip_invalid is True.

    Args:
        input_path: Path to the candidates file (.jsonl or .json).
        skip_invalid: If True, log and skip invalid records instead of raising.

    Yields:
        CandidateProfile instances, one per valid record.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If skip_invalid is False and a record fails validation,
            or if the file extension is unsupported.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    ext = input_path.suffix.lower()
    if ext == ".json":
        yield from _load_json_array(input_path, skip_invalid=skip_invalid)
    elif ext == ".jsonl":
        yield from _load_jsonl(input_path, skip_invalid=skip_invalid)
    else:
        raise ValueError(
            f"Unsupported file extension '{ext}'. Use .jsonl or .json."
        )


def _load_jsonl(
    jsonl_path: Path,
    *,
    skip_invalid: bool = True,
) -> Iterator[CandidateProfile]:
    """Stream candidate profiles from a JSONL file (one record per line)."""
    error_count = 0
    line_number = 0

    with open(jsonl_path, "rb") as fh:
        for raw_line in fh:
            line_number += 1
            raw_line = raw_line.strip()
            if not raw_line:
                continue

            try:
                data = orjson.loads(raw_line)
                candidate = CandidateProfile.model_validate(data)
                yield candidate
            except Exception as exc:
                error_count += 1
                if skip_invalid:
                    logger.warning(
                        "Skipping invalid record at line %d: %s",
                        line_number,
                        str(exc)[:200],
                    )
                else:
                    raise ValueError(
                        f"Invalid record at line {line_number}: {exc}"
                    ) from exc

    if error_count > 0:
        logger.info(
            "Finished reading %s: %d lines processed, %d errors skipped.",
            jsonl_path.name,
            line_number,
            error_count,
        )


def _load_json_array(
    json_path: Path,
    *,
    skip_invalid: bool = True,
) -> Iterator[CandidateProfile]:
    """Load candidate profiles from a JSON array file."""
    raw = json_path.read_bytes()
    records = orjson.loads(raw)

    if not isinstance(records, list):
        raise ValueError(
            f"Expected a JSON array in {json_path.name}, got {type(records).__name__}."
        )

    error_count = 0
    for idx, data in enumerate(records):
        try:
            candidate = CandidateProfile.model_validate(data)
            yield candidate
        except Exception as exc:
            error_count += 1
            if skip_invalid:
                logger.warning(
                    "Skipping invalid record at index %d: %s",
                    idx,
                    str(exc)[:200],
                )
            else:
                raise ValueError(
                    f"Invalid record at index {idx}: {exc}"
                ) from exc

    if error_count > 0:
        logger.info(
            "Finished reading %s: %d records processed, %d errors skipped.",
            json_path.name,
            len(records),
            error_count,
        )


# ══════════════════════════════════════════════════════════════════
# NPY Writer / Loader (from storage/npy_writer.py)
# ══════════════════════════════════════════════════════════════════


def save_embeddings(
    vectors: np.ndarray,
    candidate_ids: list[str],
    output_dir: Path,
) -> tuple[Path, Path]:
    """Save embeddings and candidate IDs to .npy files.

    Creates the output directory if it does not exist.
    Writes two files:
        - embeddings.npy: float32 array of shape (N, D)
        - candidate_ids.npy: Unicode string array of shape (N,)

    Args:
        vectors: Embedding matrix of shape (N, D), dtype float32.
        candidate_ids: List of candidate ID strings, length N.
        output_dir: Directory to write output files.

    Returns:
        Tuple of (embeddings_path, ids_path).

    Raises:
        ValueError: If vectors and candidate_ids have mismatched lengths.
    """
    if vectors.shape[0] != len(candidate_ids):
        raise ValueError(
            f"Shape mismatch: {vectors.shape[0]} vectors vs "
            f"{len(candidate_ids)} candidate IDs."
        )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    embeddings_path = output_dir / "embeddings.npy"
    ids_path = output_dir / "candidate_ids.npy"

    # Ensure float32 before saving.
    vectors = vectors.astype(np.float32)

    np.save(embeddings_path, vectors)
    logger.info(
        "Saved embeddings: %s (shape=%s, dtype=%s, size=%.1f MB)",
        embeddings_path,
        vectors.shape,
        vectors.dtype,
        vectors.nbytes / (1024 * 1024),
    )

    ids_array = np.array(candidate_ids, dtype=str)
    np.save(ids_path, ids_array)
    logger.info(
        "Saved candidate IDs: %s (count=%d)",
        ids_path,
        len(candidate_ids),
    )

    return embeddings_path, ids_path


def load_embeddings(output_dir: Path) -> tuple[np.ndarray, np.ndarray]:
    """Load embeddings and candidate IDs from .npy files.

    Args:
        output_dir: Directory containing embeddings.npy and candidate_ids.npy.

    Returns:
        Tuple of (embeddings_array, candidate_ids_array).

    Raises:
        FileNotFoundError: If either .npy file is missing.
        ValueError: If the arrays have mismatched first dimensions.
    """
    output_dir = Path(output_dir)

    embeddings_path = output_dir / "embeddings.npy"
    ids_path = output_dir / "candidate_ids.npy"

    if not embeddings_path.exists():
        raise FileNotFoundError(f"Embeddings file not found: {embeddings_path}")
    if not ids_path.exists():
        raise FileNotFoundError(f"Candidate IDs file not found: {ids_path}")

    vectors = np.load(embeddings_path)
    candidate_ids = np.load(ids_path)

    if vectors.shape[0] != candidate_ids.shape[0]:
        raise ValueError(
            f"Alignment mismatch: {vectors.shape[0]} embeddings vs "
            f"{candidate_ids.shape[0]} candidate IDs."
        )

    logger.info(
        "Loaded embeddings: shape=%s | candidate IDs: count=%d",
        vectors.shape,
        candidate_ids.shape[0],
    )

    return vectors, candidate_ids


# ══════════════════════════════════════════════════════════════════
# Metadata Writer (from storage/metadata_writer.py)
# ══════════════════════════════════════════════════════════════════


def write_metadata(
    output_dir: Path,
    *,
    model: str,
    dimension: int,
    normalized: bool,
    records_processed: int,
    device: str = "cpu",
    input_file: str = "",
) -> Path:
    """Write embedding metadata to a JSON file.

    Creates a metadata.json file in the output directory with
    information about the generated embeddings.

    Args:
        output_dir: Directory to write metadata.json.
        model: HuggingFace model identifier used for embedding.
        dimension: Dimensionality of the embedding vectors.
        normalized: Whether vectors are L2-normalized.
        records_processed: Total number of candidates embedded.
        device: Compute device used ('cuda' or 'cpu').
        input_file: Path to the source JSONL file.

    Returns:
        Path to the written metadata.json file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "model": model,
        "dimension": dimension,
        "normalized": normalized,
        "device": device,
        "records_processed": records_processed,
        "input_file": input_file,
        "timestamp": datetime.now(tz=UTC).isoformat(),
    }

    metadata_path = output_dir / "metadata.json"

    with open(metadata_path, "wb") as fh:
        fh.write(orjson.dumps(metadata, option=orjson.OPT_INDENT_2))

    logger.info("Wrote metadata: %s", metadata_path)

    return metadata_path


# ══════════════════════════════════════════════════════════════════
# Checkpoint Manager (from pipeline/checkpoint.py)
# ══════════════════════════════════════════════════════════════════


@dataclass
class CheckpointState:
    """Snapshot of pipeline progress at the last completed checkpoint."""

    last_batch: int
    records_processed: int
    input_path: str
    batches: list[str] = field(default_factory=list)


class CheckpointManager:
    """Manages batch checkpoints for crash recovery.

    Args:
        output_dir: Root output directory. Checkpoints are stored in
            ``output_dir/checkpoints/``.
    """

    _STATE_FILE = "checkpoint_state.json"

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = Path(output_dir)
        self._checkpoint_dir = self._output_dir / "checkpoints"
        self._checkpoint_dir.mkdir(parents=True, exist_ok=True)

    @property
    def checkpoint_dir(self) -> Path:
        """Return the checkpoint directory path."""
        return self._checkpoint_dir

    # ── Save ──────────────────────────────────────────────────────

    def save_checkpoint(
        self,
        batch_idx: int,
        embeddings: np.ndarray,
        candidate_ids: list[str],
        input_path: str,
        records_processed: int,
    ) -> Path:
        """Persist a batch checkpoint to disk.

        Args:
            batch_idx: 1-based batch ordinal.
            embeddings: Embedding matrix for this batch, shape ``(B, D)``.
            candidate_ids: Candidate ID strings for this batch.
            input_path: Original JSONL input path (for resume validation).
            records_processed: Cumulative records processed including this batch.

        Returns:
            Path to the saved ``.npz`` file.
        """
        batch_name = f"batch_{batch_idx:04d}.npz"
        batch_path = self._checkpoint_dir / batch_name

        np.savez_compressed(
            batch_path,
            embeddings=embeddings.astype(np.float32),
            candidate_ids=np.array(candidate_ids, dtype=str),
        )

        # Update state file.
        state = self._load_state_raw()
        state["last_batch"] = batch_idx
        state["records_processed"] = records_processed
        state["input_path"] = input_path
        if batch_name not in state.get("batches", []):
            state.setdefault("batches", []).append(batch_name)
        self._write_state(state)

        logger.info(
            "Checkpoint saved: %s (%d records so far)",
            batch_name,
            records_processed,
        )
        return batch_path

    # ── Load ──────────────────────────────────────────────────────

    def load_checkpoint(self) -> CheckpointState | None:
        """Load the most recent checkpoint state.

        Returns:
            A ``CheckpointState`` if a valid checkpoint exists, else ``None``.
        """
        state_path = self._checkpoint_dir / self._STATE_FILE
        if not state_path.exists():
            logger.info("No checkpoint found in %s", self._checkpoint_dir)
            return None

        raw = orjson.loads(state_path.read_bytes())
        state = CheckpointState(
            last_batch=raw["last_batch"],
            records_processed=raw["records_processed"],
            input_path=raw["input_path"],
            batches=raw.get("batches", []),
        )
        logger.info(
            "Loaded checkpoint: %d batches, %d records processed.",
            state.last_batch,
            state.records_processed,
        )
        return state

    def load_batch_data(
        self,
        state: CheckpointState,
    ) -> tuple[list[np.ndarray], list[str]]:
        """Load all checkpoint batch arrays.

        Args:
            state: Checkpoint state from ``load_checkpoint()``.

        Returns:
            Tuple of (list of embedding arrays, flat list of candidate IDs).
        """
        all_embeddings: list[np.ndarray] = []
        all_ids: list[str] = []

        for batch_name in sorted(state.batches):
            batch_path = self._checkpoint_dir / batch_name
            if not batch_path.exists():
                logger.warning("Missing checkpoint batch file: %s", batch_path)
                continue
            data = np.load(batch_path)
            all_embeddings.append(data["embeddings"])
            all_ids.extend(data["candidate_ids"].tolist())

        logger.info(
            "Loaded %d checkpoint batches (%d total records).",
            len(all_embeddings),
            len(all_ids),
        )
        return all_embeddings, all_ids

    # ── Cleanup ───────────────────────────────────────────────────

    def clear_checkpoints(self) -> None:
        """Remove all checkpoint files and the state file."""
        for f in self._checkpoint_dir.iterdir():
            f.unlink()
        logger.info("Cleared all checkpoints in %s", self._checkpoint_dir)

    # ── Internal ──────────────────────────────────────────────────

    def _load_state_raw(self) -> dict:
        """Load raw state dict, or return empty dict."""
        state_path = self._checkpoint_dir / self._STATE_FILE
        if state_path.exists():
            return dict(orjson.loads(state_path.read_bytes()))
        return {}

    def _write_state(self, state: dict) -> None:
        """Write state dict to JSON."""
        state_path = self._checkpoint_dir / self._STATE_FILE
        state_path.write_bytes(
            orjson.dumps(state, option=orjson.OPT_INDENT_2)
        )
