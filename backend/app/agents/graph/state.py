from typing import Any, TypedDict


class CareerPilotState(TypedDict, total=False):
    resume_file_path: str
    linkedin_file_path: str
    linkedin_text: str
    job_title: str
    company_name: str
    job_link: str
    job_description: str
    github_url: str
    github_input: str
    portfolio_url: str
    user_id: int
    job_id: int
    graph_run_id: str
    resume_text: str
    linkedin_profile_text: str
    github_evidence_text: str
    github_evidence_report: dict[str, Any]
    portfolio_evidence_text: str
    rag_context: str
    job_research: dict[str, Any]
    resume_analysis: dict[str, Any]
    linkedin_optimization: dict[str, Any]
    evidence_report: dict[str, Any]
    skill_gap_report: dict[str, Any]
    tailored_resume_bullets: dict[str, Any]
    recommended_projects: dict[str, Any]
    cover_letter: dict[str, Any]
    evaluation_report: dict[str, Any]
    approval_status: str
    approved_outputs: dict[str, Any]
    tracker_record: dict[str, Any]
    errors: list[dict[str, str]]
    current_step: str
    auto_approve: bool
