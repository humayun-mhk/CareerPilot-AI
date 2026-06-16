from typing import Any

from ..agents.graph.workflow import run_careerpilot_workflow
from .rag_memory import rag_memory
from ..utils.tracing import create_graph_run_id


def run_full_analysis(input_state: dict[str, Any]) -> dict[str, Any]:
    query = " ".join(
        [
            input_state.get("job_title", ""),
            input_state.get("company_name", ""),
            input_state.get("job_description", ""),
        ]
    )
    approved_context = rag_memory.retrieve_context(query)
    github_context = rag_memory.retrieve_github_context(query)
    input_state["rag_context"] = "\n".join(part for part in [approved_context, github_context] if part)
    input_state["approval_status"] = "pending"
    input_state["errors"] = input_state.get("errors", [])
    input_state["user_id"] = int(input_state.get("user_id", 1) or 1)
    input_state["graph_run_id"] = input_state.get("graph_run_id") or create_graph_run_id()

    return run_careerpilot_workflow(input_state)


def agent_outputs_for_logging(state: dict[str, Any]) -> list[tuple[str, Any]]:
    return [
        ("job_research_agent", state.get("job_research", {})),
        ("resume_analyzer_agent", state.get("resume_analysis", {})),
        ("linkedin_optimizer_agent", state.get("linkedin_optimization", {})),
        ("github_evidence_agent", state.get("github_evidence_report", {})),
        ("skill_gap_agent", state.get("skill_gap_report", {})),
        ("evidence_verification_agent", state.get("evidence_report", {})),
        ("resume_tailoring_agent", state.get("tailored_resume_bullets", {})),
        ("project_recommender_agent", state.get("recommended_projects", {})),
        ("cover_letter_agent", state.get("cover_letter", {})),
        ("evaluation_agent", state.get("evaluation_report", {})),
    ]
