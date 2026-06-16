from typing import Any, Literal

from pydantic import BaseModel, Field


ApplicationStatus = Literal[
    "Saved",
    "Ready to Apply",
    "Applied",
    "Follow-up Needed",
    "Interview",
    "Rejected",
    "Offer",
]


class AnalysisResponse(BaseModel):
    analysis_id: int
    state: dict[str, Any]


class ApprovalRequest(BaseModel):
    decision: Literal["approved", "rejected"] = "approved"
    approved_resume_bullets: list[str] = Field(default_factory=list)
    approved_cover_letter: str = ""


class ApprovalResponse(BaseModel):
    analysis_id: int
    approval_status: str
    application_id: int | None = None
    tracker_record: dict[str, Any] = Field(default_factory=dict)


class StatusUpdateRequest(BaseModel):
    status: ApplicationStatus


class ApiMessage(BaseModel):
    message: str
