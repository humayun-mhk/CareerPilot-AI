from datetime import date, timedelta

from src.database.db import save_agent_run, save_application_record, save_evidence_report


def _agent_outputs_for_logging(state: dict) -> list[tuple[str, dict]]:
    return [
        ("job_research_agent", state.get("job_research", {})),
        ("resume_analyzer_agent", state.get("resume_analysis", {})),
        ("linkedin_optimizer_agent", state.get("linkedin_optimization", {})),
        ("evidence_verification_agent", state.get("evidence_report", {})),
        ("skill_gap_agent", state.get("skill_gap_report", {})),
        ("resume_tailoring_agent", state.get("tailored_resume_bullets", {})),
        ("project_recommender_agent", state.get("recommended_projects", {})),
        ("cover_letter_agent", state.get("cover_letter", {})),
    ]


def run_tracker_agent(state: dict) -> dict:
    if state.get("approval_status") != "approved":
        return {
            "tracker_record": {
                "saved": False,
                "status": "Pending Approval",
                "message": "Human approval is required before saving final outputs.",
            },
            "current_step": "tracker_agent",
        }

    approved = state.get("approved_outputs") or {}
    follow_up_date = (date.today() + timedelta(days=7)).isoformat()
    match_score = (state.get("skill_gap_report") or {}).get("overall_match", 0)
    record = {
        "company_name": state.get("company_name", ""),
        "job_title": state.get("job_title", ""),
        "job_link": state.get("job_link", ""),
        "job_description": state.get("job_description", ""),
        "match_score": match_score,
        "status": "Ready to Apply",
        "follow_up_date": follow_up_date,
        "approved_resume_bullets": approved.get("resume_bullets", []),
        "approved_cover_letter": approved.get("cover_letter", ""),
    }

    application_id = save_application_record(record)
    for skill_name, details in (state.get("evidence_report") or {}).items():
        save_evidence_report(application_id, skill_name, details)
    for step_name, output in _agent_outputs_for_logging(state):
        save_agent_run(application_id, step_name, {}, output)

    return {
        "tracker_record": {
            "id": application_id,
            "company_name": record["company_name"],
            "job_title": record["job_title"],
            "job_link": record["job_link"],
            "match_score": match_score,
            "status": record["status"],
            "follow_up_date": follow_up_date,
            "saved": True,
        },
        "current_step": "tracker_agent",
    }
