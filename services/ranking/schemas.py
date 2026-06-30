from typing import Any, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

class CandidateInput(BaseModel):
    """
    Schema for validating candidate data received from upstream pipeline.
    Allows extra fields to prevent breaking changes if upstream database schemas change.
    """
    model_config = ConfigDict(extra="allow")

    id: Union[int, str] = Field(description="Unique candidate identifier")
    name: str = Field(description="Candidate's full name")
    skills: Union[str, List[str]] = Field(description="Comma-separated skills list, skill summary, or structured skills list")
    resume_text: str = Field(description="Parsed raw or semi-structured resume text")

    @field_validator("skills", mode="before")
    @classmethod
    def normalize_skills(cls, value):
        if isinstance(value, list):
            return ", ".join(str(item) for item in value)
        return value

class CandidateRanked(CandidateInput):
    """
    Schema for output candidate data, extending the input schema with the computed match score.
    """
    ai_match_score: float = Field(description="Relevance score computed by the Cross-Encoder model")

class DashboardRequest(BaseModel):
    query: Optional[str] = Field(default=None, description="Optional job description to filter/rank candidates")
    top_k: Optional[int] = Field(default=20, description="Number of top candidates to analyze")

class SkillDistribution(BaseModel):
    skill: str
    count: int

class ScoreDistribution(BaseModel):
    range: str
    label: str
    count: int
    percentage: float

class ExperienceDistribution(BaseModel):
    range: str
    label: str
    count: int

class DashboardResponse(BaseModel):
    query: str
    total_candidates: int
    skill_distribution: List[SkillDistribution]
    score_distribution: List[ScoreDistribution]
    experience_distribution: List[ExperienceDistribution]

class RerankRequest(BaseModel):
    """
    Schema representing a formal request package to rerank a list of candidates.
    """
    job_description: str = Field(description="Job description query text")
    retrieved_candidates: List[CandidateInput] = Field(
        description="List of candidates already retrieved for reranking",
        validation_alias="candidates",
    )
    cutoff_layer: Optional[int] = Field(default=12, description="Model early exit layer cutoff")
