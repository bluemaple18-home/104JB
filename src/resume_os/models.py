from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class EntityKind(StrEnum):
    BASICS = "basics"
    EXPERIENCE = "experience"
    PROJECT = "project"
    EDUCATION = "education"
    SKILL = "skill"


class Evidence(BaseModel):
    entity_id: str | None = None
    field_path: str
    source_type: Literal["104", "interview", "github", "approved_version"]
    source_ref: str
    content: str
    contribution_type: Literal[
        "fact", "owner_decision", "business_rule", "validation", "ai_assisted_implementation"
    ] = "fact"


class ChangeProposal(BaseModel):
    entity_id: str
    field_path: str
    before: Any
    after: Any
    reason: str
    evidence_ids: list[str] = Field(min_length=1)
    risk_flags: list[str] = Field(default_factory=list)
    status: Literal["pending", "accepted", "rejected", "edited", "blocked"] = "pending"
