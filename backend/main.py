from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.config import ALLOWED_ORIGINS, UPLOAD_DIR
from backend.database import (
    get_all_applications,
    get_analysis_run,
    get_analytics,
    get_evidence_graph,
    init_db,
    save_agent_run,
    save_analysis_run,
    save_application_record,
    save_evidence_report,
    update_analysis_run,
    update_application_status,
)
from backend.rag_memory import rag_memory
from backend.schemas import (
    AnalysisResponse,
    ApiMessage,
    ApprovalRequest,
    ApprovalResponse,
    StatusUpdateRequest,
)
from backend.workflow_service import agent_outputs_for_logging, run_full_analysis


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    rag_memory.init()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="CareerPilot AI API", version="3.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _safe_upload_name(filename: str) -> str:
    clean = "".join(char if char.isalnum() or char in "._-" else "_" for char in filename)
    return clean.strip("._") or "upload.pdf"


async def _save_upload(upload: UploadFile | None, folder: str) -> str:
    if upload is None:
        return ""
    if not upload.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail=f"{upload.filename} must be a PDF file.")
    target_dir = UPLOAD_DIR / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    target_path = target_dir / f"{timestamp}_{_safe_upload_name(upload.filename)}"
    content = await upload.read()
    if not content:
        raise HTTPException(status_code=400, detail=f"{upload.filename} is empty.")
    target_path.write_bytes(content)
    return str(target_path)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "CareerPilot AI API", "chroma_available": rag_memory.available}


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(
    resume_file: Annotated[UploadFile, File()],
    linkedin_file: Annotated[UploadFile | None, File()] = None,
    linkedin_text: Annotated[str, Form()] = "",
    job_title: Annotated[str, Form()] = "",
    company_name: Annotated[str, Form()] = "",
    job_link: Annotated[str, Form()] = "",
    job_description: Annotated[str, Form()] = "",
    github_url: Annotated[str, Form()] = "",
    portfolio_url: Annotated[str, Form()] = "",
) -> AnalysisResponse:
    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description is required.")
    if linkedin_file is None and not linkedin_text.strip():
        raise HTTPException(status_code=400, detail="LinkedIn PDF or LinkedIn text is required.")

    resume_path = await _save_upload(resume_file, "resumes")
    linkedin_path = await _save_upload(linkedin_file, "linkedin") if linkedin_file else ""
    initial_state = {
        "resume_file_path": resume_path,
        "linkedin_file_path": linkedin_path,
        "linkedin_text": linkedin_text,
        "job_title": job_title,
        "company_name": company_name,
        "job_link": job_link,
        "job_description": job_description,
        "github_url": github_url,
        "portfolio_url": portfolio_url,
    }
    try:
        state = run_full_analysis(initial_state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"LangGraph analysis failed: {exc}") from exc

    analysis_id = save_analysis_run(initial_state, state)
    return AnalysisResponse(analysis_id=analysis_id, state=state)


@app.get("/api/analysis/{analysis_id}")
def get_analysis(analysis_id: int) -> dict:
    analysis = get_analysis_run(analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return analysis


@app.post("/api/approvals/{analysis_id}", response_model=ApprovalResponse)
def approve_analysis(analysis_id: int, payload: ApprovalRequest) -> ApprovalResponse:
    analysis = get_analysis_run(analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    state = analysis["output"]
    if payload.decision == "rejected":
        state["approval_status"] = "rejected"
        update_analysis_run(analysis_id, state, "rejected", analysis.get("application_id"))
        return ApprovalResponse(analysis_id=analysis_id, approval_status="rejected")

    if analysis.get("application_id"):
        return ApprovalResponse(
            analysis_id=analysis_id,
            approval_status="approved",
            application_id=analysis["application_id"],
            tracker_record=state.get("tracker_record", {}),
        )

    approved_outputs = {
        "resume_bullets": payload.approved_resume_bullets,
        "cover_letter": payload.approved_cover_letter,
    }
    state["approval_status"] = "approved"
    state["approved_outputs"] = approved_outputs
    application_id = save_application_record(state, approved_outputs)

    for skill_name, details in (state.get("evidence_report") or {}).items():
        save_evidence_report(application_id, skill_name, details)
    for step_name, output in agent_outputs_for_logging(state):
        save_agent_run(application_id, step_name, {}, output)

    metadata = {
        "company_name": state.get("company_name", ""),
        "job_title": state.get("job_title", ""),
        "job_link": state.get("job_link", ""),
    }
    rag_memory.add_approved_content(
        application_id,
        approved_outputs["resume_bullets"],
        approved_outputs["cover_letter"],
        metadata,
    )
    rag_memory.add_evidence_report(application_id, state.get("evidence_report") or {})

    tracker_record = {
        "id": application_id,
        "company_name": state.get("company_name", ""),
        "job_title": state.get("job_title", ""),
        "job_link": state.get("job_link", ""),
        "match_score": (state.get("skill_gap_report") or {}).get("overall_match", 0),
        "status": "Ready to Apply",
        "saved": True,
    }
    state["tracker_record"] = tracker_record
    update_analysis_run(analysis_id, state, "approved", application_id)
    return ApprovalResponse(
        analysis_id=analysis_id,
        approval_status="approved",
        application_id=application_id,
        tracker_record=tracker_record,
    )


@app.get("/api/applications")
def applications() -> list[dict]:
    return get_all_applications()


@app.patch("/api/applications/{application_id}/status", response_model=ApiMessage)
def update_status(application_id: int, payload: StatusUpdateRequest) -> ApiMessage:
    updated = update_application_status(application_id, payload.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Application not found.")
    return ApiMessage(message="Application status updated.")


@app.get("/api/analytics")
def analytics() -> dict:
    return get_analytics()


@app.get("/api/evidence-graph")
def evidence_graph(application_id: int | None = None) -> dict:
    return get_evidence_graph(application_id)


@app.get("/api/memory/search")
def memory_search(query: str, limit: int = 5) -> dict:
    return {"query": query, "context": rag_memory.retrieve_context(query, limit)}
