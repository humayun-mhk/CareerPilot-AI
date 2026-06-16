from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ApplicationRecord(BaseModel):
    company_name: str = ""
    job_title: str = ""
    job_link: str = ""
    job_description: str = ""
    match_score: float = 0
    status: str = "Saved"
    follow_up_date: str = ""
    approved_resume_bullets: list[str] = Field(default_factory=list)
    approved_cover_letter: str = ""


class AgentRunRecord(BaseModel):
    application_id: int
    step_name: str
    input_json: dict[str, Any] = Field(default_factory=dict)
    output_json: dict[str, Any] = Field(default_factory=dict)


class EvidenceReportRecord(BaseModel):
    application_id: int
    skill_name: str
    evidence_json: list[str] = Field(default_factory=list)
    confidence: float = 0
    status: str = "missing"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(timespec="seconds"))
