from sqlalchemy import Float, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_name: Mapped[str | None] = mapped_column(Text)
    job_title: Mapped[str | None] = mapped_column(Text)
    job_link: Mapped[str | None] = mapped_column(Text)
    job_description: Mapped[str | None] = mapped_column(Text)
    match_score: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str | None] = mapped_column(Text)
    follow_up_date: Mapped[str | None] = mapped_column(Text)
    approved_resume_bullets: Mapped[str | None] = mapped_column(Text)
    approved_cover_letter: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[str | None] = mapped_column(Text)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id"))
    step_name: Mapped[str | None] = mapped_column(Text)
    input_json: Mapped[str | None] = mapped_column(Text)
    output_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str | None] = mapped_column(Text)


class EvidenceReport(Base):
    __tablename__ = "evidence_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id"))
    skill_name: Mapped[str | None] = mapped_column(Text)
    evidence_json: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str | None] = mapped_column(Text)


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    input_json: Mapped[str] = mapped_column(Text)
    output_json: Mapped[str] = mapped_column(Text)
    approval_status: Mapped[str] = mapped_column(Text)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id"))
    created_at: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[str | None] = mapped_column(Text)


class GitHubEvidenceScan(Base):
    __tablename__ = "github_evidence_scans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer)
    username: Mapped[str | None] = mapped_column(Text)
    repositories_scanned: Mapped[int | None] = mapped_column(Integer)
    report_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str | None] = mapped_column(Text)


class GitHubRepositoryEvidence(Base):
    __tablename__ = "github_repository_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_id: Mapped[int | None] = mapped_column(ForeignKey("github_evidence_scans.id"))
    user_id: Mapped[int | None] = mapped_column(Integer)
    repo_name: Mapped[str | None] = mapped_column(Text)
    repo_url: Mapped[str | None] = mapped_column(Text)
    project_type: Mapped[str | None] = mapped_column(Text)
    detected_skills_json: Mapped[str | None] = mapped_column(Text)
    readme_summary: Mapped[str | None] = mapped_column(Text)
    evidence_confidence: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[str | None] = mapped_column(Text)


class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer)
    resume_id: Mapped[int | None] = mapped_column(Integer)
    job_id: Mapped[int | None] = mapped_column(Integer)
    version_name: Mapped[str | None] = mapped_column(Text)
    company: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str | None] = mapped_column(Text)
    original_bullets: Mapped[str | None] = mapped_column(Text)
    generated_bullets: Mapped[str | None] = mapped_column(Text)
    approved_bullets: Mapped[str | None] = mapped_column(Text)
    previous_match_score: Mapped[float | None] = mapped_column(Float)
    improved_match_score: Mapped[float | None] = mapped_column(Float)
    change_summary: Mapped[str | None] = mapped_column(Text)
    approval_status: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str | None] = mapped_column(Text)


class ResumeExport(Base):
    __tablename__ = "resume_exports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer)
    resume_version_id: Mapped[int | None] = mapped_column(ForeignKey("resume_versions.id"))
    job_id: Mapped[int | None] = mapped_column(Integer)
    file_name: Mapped[str | None] = mapped_column(Text)
    file_path: Mapped[str | None] = mapped_column(Text)
    export_format: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str | None] = mapped_column(Text)


class EvaluationReport(Base):
    __tablename__ = "evaluation_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer)
    job_id: Mapped[int | None] = mapped_column(Integer)
    application_id: Mapped[int | None] = mapped_column(Integer)
    job_match_score: Mapped[int | None] = mapped_column(Integer)
    skill_coverage_score: Mapped[int | None] = mapped_column(Integer)
    evidence_confidence_score: Mapped[int | None] = mapped_column(Integer)
    hallucination_risk_score: Mapped[int | None] = mapped_column(Integer)
    ats_keyword_score: Mapped[int | None] = mapped_column(Integer)
    cover_letter_personalization_score: Mapped[int | None] = mapped_column(Integer)
    overall_quality_score: Mapped[int | None] = mapped_column(Integer)
    issues_json: Mapped[str | None] = mapped_column(Text)
    blocked_claims_json: Mapped[str | None] = mapped_column(Text)
    recommendations_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str | None] = mapped_column(Text)


class AgentTrace(Base):
    __tablename__ = "agent_traces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    graph_run_id: Mapped[str | None] = mapped_column(Text)
    user_id: Mapped[int | None] = mapped_column(Integer)
    job_id: Mapped[int | None] = mapped_column(Integer)
    agent_name: Mapped[str | None] = mapped_column(Text)
    step_order: Mapped[int | None] = mapped_column(Integer)
    input_summary: Mapped[str | None] = mapped_column(Text)
    output_summary: Mapped[str | None] = mapped_column(Text)
    input_json: Mapped[str | None] = mapped_column(Text)
    output_json: Mapped[str | None] = mapped_column(Text)
    tools_called_json: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[str | None] = mapped_column(Text)
    ended_at: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int | None] = mapped_column(Integer)


class ApprovalItem(Base):
    __tablename__ = "approval_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer)
    application_id: Mapped[int | None] = mapped_column(Integer)
    content_type: Mapped[str | None] = mapped_column(Text)
    original_content: Mapped[str | None] = mapped_column(Text)
    edited_content: Mapped[str | None] = mapped_column(Text)
    approval_status: Mapped[str | None] = mapped_column(Text)
    reviewer_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[str | None] = mapped_column(Text)
