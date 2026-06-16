from uuid import uuid4
import warnings

import requests
from bs4 import BeautifulSoup

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.graph import END, START, StateGraph

from ..cover_letter_agent import run_cover_letter_agent
from ..evaluation_agent import run_evaluation_agent
from ..evidence_agent import run_evidence_verification_agent
from ..github_evidence_agent import run_github_evidence_agent
from ..human_approval_agent import run_human_approval_agent
from ..job_research_agent import run_job_research_agent
from ..linkedin_optimizer_agent import run_linkedin_optimizer_agent
from ..project_recommender_agent import run_project_recommender_agent
from ..resume_analyzer_agent import run_resume_analyzer_agent
from ..resume_tailoring_agent import run_resume_tailoring_agent
from ..skill_gap_agent import run_skill_gap_agent
from ..tracker_agent import run_tracker_agent
from .state import CareerPilotState
from ...utils.tools.github_tool import fetch_github_profile_text
from ...utils.tools.job_parser import clean_job_description
from ...utils.tools.linkedin_parser import parse_linkedin_pdf, parse_linkedin_text
from ...utils.tools.pdf_parser import extract_text_from_pdf
from ...utils.tracing import end_agent_trace, start_agent_trace


STEP_ORDER = {
    "document_parser_node": 1,
    "resume_analyzer_node": 2,
    "linkedin_optimizer_node": 3,
    "github_evidence_node": 4,
    "job_research_node": 5,
    "skill_gap_node": 6,
    "evidence_verification_node": 7,
    "resume_tailoring_node": 8,
    "project_recommender_node": 9,
    "cover_letter_node": 10,
    "evaluation_node": 11,
    "human_approval_node": 12,
    "tracker_node": 13,
}


def _with_error(state: dict, step: str, exc: Exception) -> dict:
    errors = list(state.get("errors", []))
    errors.append({"step": step, "message": str(exc)})
    return {"errors": errors, "current_step": step}


def _safe_node(step: str, func):
    def wrapped(state: CareerPilotState) -> dict:
        state_dict = dict(state)
        trace_id = start_agent_trace(
            graph_run_id=state_dict.get("graph_run_id", ""),
            user_id=int(state_dict.get("user_id", 1) or 1),
            job_id=state_dict.get("job_id"),
            agent_name=step,
            step_order=STEP_ORDER.get(step, 999),
            input_data=state_dict,
        )
        try:
            output = func(state_dict)
            end_agent_trace(trace_id, output, status="success")
            return output
        except Exception as exc:
            output = _with_error(state_dict, step, exc)
            end_agent_trace(trace_id, output, status="failed", error_message=str(exc))
            return output

    return wrapped


def _fetch_url_text(url: str) -> str:
    if not url:
        return ""
    try:
        response = requests.get(url, timeout=8, headers={"User-Agent": "CareerPilotAI/1.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return " ".join(soup.get_text(" ").split())[:8000]
    except Exception:
        return ""


def document_parser_node(state: dict) -> dict:
    resume_text = state.get("resume_text", "")
    if not resume_text and state.get("resume_file_path"):
        resume_text = extract_text_from_pdf(state["resume_file_path"])

    linkedin_profile_text = parse_linkedin_text(state.get("linkedin_text", ""))
    if not linkedin_profile_text and state.get("linkedin_file_path"):
        linkedin_profile_text = parse_linkedin_pdf(state["linkedin_file_path"])

    return {
        "resume_text": resume_text,
        "linkedin_profile_text": linkedin_profile_text,
        "github_evidence_text": fetch_github_profile_text(state.get("github_url", "")),
        "portfolio_evidence_text": _fetch_url_text(state.get("portfolio_url", "")),
        "job_description": clean_job_description(state.get("job_description", "")),
        "current_step": "document_parser_node",
    }


def build_careerpilot_graph():
    graph = StateGraph(CareerPilotState)
    graph.add_node("document_parser_node", _safe_node("document_parser_node", document_parser_node))
    graph.add_node("resume_analyzer_node", _safe_node("resume_analyzer_node", run_resume_analyzer_agent))
    graph.add_node("linkedin_optimizer_node", _safe_node("linkedin_optimizer_node", run_linkedin_optimizer_agent))
    graph.add_node("github_evidence_node", _safe_node("github_evidence_node", run_github_evidence_agent))
    graph.add_node("job_research_node", _safe_node("job_research_node", run_job_research_agent))
    graph.add_node("skill_gap_node", _safe_node("skill_gap_node", run_skill_gap_agent))
    graph.add_node("evidence_verification_node", _safe_node("evidence_verification_node", run_evidence_verification_agent))
    graph.add_node("resume_tailoring_node", _safe_node("resume_tailoring_node", run_resume_tailoring_agent))
    graph.add_node("project_recommender_node", _safe_node("project_recommender_node", run_project_recommender_agent))
    graph.add_node("cover_letter_node", _safe_node("cover_letter_node", run_cover_letter_agent))
    graph.add_node("evaluation_node", _safe_node("evaluation_node", run_evaluation_agent))
    graph.add_node("human_approval_node", _safe_node("human_approval_node", run_human_approval_agent))
    graph.add_node("tracker_node", _safe_node("tracker_node", run_tracker_agent))

    graph.add_edge(START, "document_parser_node")
    graph.add_edge("document_parser_node", "resume_analyzer_node")
    graph.add_edge("resume_analyzer_node", "linkedin_optimizer_node")
    graph.add_edge("linkedin_optimizer_node", "github_evidence_node")
    graph.add_edge("github_evidence_node", "job_research_node")
    graph.add_edge("job_research_node", "skill_gap_node")
    graph.add_edge("skill_gap_node", "evidence_verification_node")
    graph.add_edge("evidence_verification_node", "resume_tailoring_node")
    graph.add_edge("resume_tailoring_node", "project_recommender_node")
    graph.add_edge("project_recommender_node", "cover_letter_node")
    graph.add_edge("cover_letter_node", "evaluation_node")
    graph.add_edge("evaluation_node", "human_approval_node")
    graph.add_edge("human_approval_node", "tracker_node")
    graph.add_edge("tracker_node", END)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return graph.compile(checkpointer=MemorySaver())


def run_careerpilot_workflow(initial_state: dict) -> dict:
    app = build_careerpilot_graph()
    initial_state.setdefault("user_id", 1)
    initial_state.setdefault("graph_run_id", str(uuid4()))
    config = {"configurable": {"thread_id": initial_state.get("thread_id") or str(uuid4())}}
    return dict(app.invoke(initial_state, config=config))
