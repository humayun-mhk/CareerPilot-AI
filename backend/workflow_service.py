from typing import Any

from backend.rag_memory import rag_memory


def run_full_analysis(input_state: dict[str, Any]) -> dict[str, Any]:
    query = " ".join(
        [
            input_state.get("job_title", ""),
            input_state.get("company_name", ""),
            input_state.get("job_description", ""),
        ]
    )
    input_state["rag_context"] = rag_memory.retrieve_context(query)
    input_state["approval_status"] = "pending"
    input_state["errors"] = input_state.get("errors", [])

    from src.graph.workflow import run_careerpilot_workflow

    return run_careerpilot_workflow(input_state)


def agent_outputs_for_logging(state: dict[str, Any]) -> list[tuple[str, Any]]:
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
