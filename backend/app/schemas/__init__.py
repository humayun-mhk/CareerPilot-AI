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


class GitHubScanRequest(BaseModel):
    user_id: int = 1
    github_input: str


class ResumeVersionCreateRequest(BaseModel):
    user_id: int = 1
    resume_id: int | None = None
    job_id: int | None = None
    version_name: str = ""
    company: str = ""
    role: str = ""
    original_bullets: list[str] = Field(default_factory=list)
    generated_bullets: list[str] = Field(default_factory=list)
    approved_bullets: list[str] = Field(default_factory=list)
    previous_match_score: float = 0
    improved_match_score: float = 0
    change_summary: str = ""
    approval_status: str = "pending"


class ResumeExportRequest(BaseModel):
    user_id: int = 1
    version_id: int
    export_format: Literal["pdf", "txt", "markdown"] = "pdf"


class ResumeCompareRequest(BaseModel):
    version_a_id: int
    version_b_id: int


class ApprovalActionRequest(BaseModel):
    approval_id: int
    edited_content: str = ""
    reviewer_notes: str = ""


class ApprovalCreateRequest(BaseModel):
    user_id: int = 1
    application_id: int | None = None
    content_type: str
    original_content: str
    edited_content: str = ""
