from uuid import uuid4
import warnings

import requests
from bs4 import BeautifulSoup

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.graph import END, START, StateGraph

from src.agents.cover_letter_agent import run_cover_letter_agent
from src.agents.evidence_agent import run_evidence_verification_agent
from src.agents.human_approval_agent import run_human_approval_agent
from src.agents.job_research_agent import run_job_research_agent
from src.agents.linkedin_optimizer_agent import run_linkedin_optimizer_agent
from src.agents.project_recommender_agent import run_project_recommender_agent
from src.agents.resume_analyzer_agent import run_resume_analyzer_agent
from src.agents.resume_tailoring_agent import run_resume_tailoring_agent
from src.agents.skill_gap_agent import run_skill_gap_agent
from src.agents.tracker_agent import run_tracker_agent
from src.graph.state import CareerPilotState
from src.tools.github_tool import fetch_github_profile_text
from src.tools.job_parser import clean_job_description
from src.tools.linkedin_parser import parse_linkedin_pdf, parse_linkedin_text
from src.tools.pdf_parser import extract_text_from_pdf


def _with_error(state: dict, step: str, exc: Exception) -> dict:
    errors = list(state.get("errors", []))
    errors.append({"step": step, "message": str(exc)})
    return {"errors": errors, "current_step": step}


def _safe_node(step: str, func):
    def wrapped(state: CareerPilotState) -> dict:
        try:
            return func(dict(state))
        except Exception as exc:
            return _with_error(dict(state), step, exc)

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
    graph.add_node("job_research_node", _safe_node("job_research_node", run_job_research_agent))
    graph.add_node("evidence_verification_node", _safe_node("evidence_verification_node", run_evidence_verification_agent))
    graph.add_node("skill_gap_node", _safe_node("skill_gap_node", run_skill_gap_agent))
    graph.add_node("resume_tailoring_node", _safe_node("resume_tailoring_node", run_resume_tailoring_agent))
    graph.add_node("project_recommender_node", _safe_node("project_recommender_node", run_project_recommender_agent))
    graph.add_node("cover_letter_node", _safe_node("cover_letter_node", run_cover_letter_agent))
    graph.add_node("human_approval_node", _safe_node("human_approval_node", run_human_approval_agent))
    graph.add_node("tracker_node", _safe_node("tracker_node", run_tracker_agent))

    graph.add_edge(START, "document_parser_node")
    graph.add_edge("document_parser_node", "resume_analyzer_node")
    graph.add_edge("resume_analyzer_node", "linkedin_optimizer_node")
    graph.add_edge("linkedin_optimizer_node", "job_research_node")
    graph.add_edge("job_research_node", "evidence_verification_node")
    graph.add_edge("evidence_verification_node", "skill_gap_node")
    graph.add_edge("skill_gap_node", "resume_tailoring_node")
    graph.add_edge("resume_tailoring_node", "project_recommender_node")
    graph.add_edge("project_recommender_node", "cover_letter_node")
    graph.add_edge("cover_letter_node", "human_approval_node")
    graph.add_edge("human_approval_node", "tracker_node")
    graph.add_edge("tracker_node", END)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return graph.compile(checkpointer=MemorySaver())


def run_careerpilot_workflow(initial_state: dict) -> dict:
    app = build_careerpilot_graph()
    config = {"configurable": {"thread_id": initial_state.get("thread_id") or str(uuid4())}}
    return dict(app.invoke(initial_state, config=config))
