from datetime import datetime
import logging
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ...core.config import DATABASE_DRIVER, UPLOAD_DIR
from ...db.session import (
    get_all_applications,
    get_analysis_run,
    get_analytics,
    get_evaluation_detail,
    get_evaluations,
    get_evidence_graph,
    save_agent_run,
    save_analysis_run,
    save_application_record,
    save_evaluation_report,
    save_evidence_report,
    save_github_evidence_scan,
    update_analysis_run,
    update_application_status,
)
from ...schemas import (
    AnalysisResponse,
    ApiMessage,
    ApprovalActionRequest,
    ApprovalCreateRequest,
    ApprovalRequest,
    ApprovalResponse,
    GitHubScanRequest,
    ResumeCompareRequest,
    ResumeExportRequest,
    ResumeVersionCreateRequest,
    StatusUpdateRequest,
)
from ...services.approval_service import (
    approve_content,
    create_pending_approval,
    get_approval_history,
    get_pending_approvals,
    reject_content,
    request_regeneration,
)
from ...services.rag_memory import rag_memory
from ...services.resume_versioning import (
    compare_resume_versions,
    create_resume_version,
    export_resume_version_pdf,
    export_resume_version_txt,
    get_resume_version_detail,
    get_resume_versions,
    update_resume_version_approval,
)
from ...services.workflow_service import agent_outputs_for_logging, run_full_analysis
from ...utils.github_scanner import scan_github_evidence
from ...utils.tracing import get_agent_traces, get_graph_run_trace


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("careerpilot.api")
router = APIRouter()


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


def _create_step4_approval_items(user_id: int, application_id: int | None, state: dict) -> None:
    bullets = (state.get("tailored_resume_bullets") or {}).get("tailored_bullets", [])
    linkedin = state.get("linkedin_optimization") or {}
    cover_letter = (state.get("cover_letter") or {}).get("cover_letter", "")
    items = [
        ("resume_bullets", "\n".join(bullets)),
        ("linkedin_headline", linkedin.get("new_headline", "") or linkedin.get("headline", "")),
        ("linkedin_about", linkedin.get("improved_about_section", "") or linkedin.get("about_section", "")),
        ("cover_letter", cover_letter),
        ("resume_pdf_export", f"Resume version {state.get('resume_version_id', '')} export approval"),
    ]
    for content_type, original_content in items:
        if original_content:
            create_pending_approval(user_id, application_id, content_type, original_content)


@router.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "CareerPilot AI API", "chroma_available": rag_memory.available}


@router.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(
    resume_file: Annotated[UploadFile, File()],
    user_id: Annotated[int, Form()] = 1,
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
        "user_id": user_id,
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
        logger.exception("LangGraph analysis failed")
        raise HTTPException(status_code=500, detail=f"LangGraph analysis failed: {exc}") from exc

    analysis_id = save_analysis_run(initial_state, state)
    github_report = state.get("github_evidence_report") or {}
    if github_report.get("projects"):
        scan_id = save_github_evidence_scan(user_id, github_report)
        github_report["scan_id"] = scan_id
        rag_memory.add_github_readme_chunks(user_id, github_report)
    evaluation_report = state.get("evaluation_report") or {}
    if evaluation_report:
        evaluation_report["user_id"] = user_id
        state["evaluation_report_id"] = save_evaluation_report(evaluation_report)
    tailored_bullets = (state.get("tailored_resume_bullets") or {}).get("tailored_bullets", [])
    original_bullets = (state.get("resume_analysis") or {}).get("projects", [])
    if tailored_bullets:
        state["resume_version_id"] = create_resume_version(
            user_id=user_id,
            job_id=None,
            company=state.get("company_name", ""),
            role=state.get("job_title", ""),
            original_bullets=original_bullets,
            generated_bullets=tailored_bullets,
            approved_bullets=[],
            previous_match_score=(state.get("skill_gap_report") or {}).get("overall_match", 0),
            improved_match_score=(state.get("evaluation_report") or {}).get("overall_quality_score", 0),
            change_summary="Initial tailored resume version generated by CareerPilot AI.",
            approval_status="pending",
        )
    _create_step4_approval_items(user_id, None, state)
    update_analysis_run(analysis_id, state, state.get("approval_status", "pending"), None)
    return AnalysisResponse(analysis_id=analysis_id, state=state)


@router.get("/api/analysis/{analysis_id}")
def get_analysis(analysis_id: int) -> dict:
    analysis = get_analysis_run(analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return analysis


@router.post("/api/approvals/{analysis_id}", response_model=ApprovalResponse)
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
    if state.get("resume_version_id"):
        update_resume_version_approval(
            int(state["resume_version_id"]),
            payload.approved_resume_bullets,
            "approved",
        )
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


@router.get("/api/applications")
def applications() -> list[dict]:
    return get_all_applications()


@router.patch("/api/applications/{application_id}/status", response_model=ApiMessage)
def update_status(application_id: int, payload: StatusUpdateRequest) -> ApiMessage:
    updated = update_application_status(application_id, payload.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Application not found.")
    return ApiMessage(message="Application status updated.")


@router.get("/api/analytics")
def analytics() -> dict:
    return get_analytics()


@router.get("/api/evidence-graph")
def evidence_graph(application_id: int | None = None) -> dict:
    return get_evidence_graph(application_id)


@router.get("/api/memory/search")
def memory_search(query: str, limit: int = 5) -> dict:
    return {"query": query, "context": rag_memory.retrieve_context(query, limit)}


@router.post("/github/scan")
@router.post("/api/github/scan")
def github_scan(payload: GitHubScanRequest) -> dict:
    report = scan_github_evidence(payload.github_input)
    scan_id = save_github_evidence_scan(payload.user_id, report)
    report["scan_id"] = scan_id
    rag_memory.add_github_readme_chunks(payload.user_id, report)
    return report


@router.get("/api/resume-versions/{user_id}")
@router.get("/resume-versions/{user_id}")
def resume_versions(user_id: int) -> list[dict]:
    return get_resume_versions(user_id)


@router.post("/api/resume-versions")
def create_resume_version_endpoint(payload: ResumeVersionCreateRequest) -> dict:
    version_id = create_resume_version(**payload.model_dump())
    detail = get_resume_version_detail(version_id)
    return detail or {"id": version_id}


@router.get("/api/resume-versions/detail/{version_id}")
@router.get("/resume-versions/detail/{version_id}")
def resume_version_detail(version_id: int) -> dict:
    detail = get_resume_version_detail(version_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Resume version not found.")
    return detail


@router.post("/api/resume-versions/compare")
def resume_version_compare(payload: ResumeCompareRequest) -> dict:
    return compare_resume_versions(payload.version_a_id, payload.version_b_id)


@router.post("/api/resume-versions/export")
@router.post("/resume-versions/export")
def resume_version_export(payload: ResumeExportRequest) -> dict:
    detail = get_resume_version_detail(payload.version_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Resume version not found.")
    if detail.get("approval_status") not in {"approved", "edited"}:
        raise HTTPException(status_code=403, detail="Resume export requires human approval first.")
    if payload.export_format == "pdf":
        result = export_resume_version_pdf(payload.version_id, payload.user_id)
    else:
        result = export_resume_version_txt(payload.version_id, payload.user_id, payload.export_format)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/api/evaluations/{user_id}")
@router.get("/evaluations/{user_id}")
def evaluations(user_id: int) -> list[dict]:
    return get_evaluations(user_id)


@router.get("/api/evaluations/detail/{evaluation_id}")
@router.get("/evaluations/detail/{evaluation_id}")
def evaluation_detail(evaluation_id: int) -> dict:
    detail = get_evaluation_detail(evaluation_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Evaluation report not found.")
    return detail


@router.get("/api/traces/{user_id}")
@router.get("/traces/{user_id}")
def traces(user_id: int) -> list[dict]:
    return get_agent_traces(user_id)


@router.get("/api/traces/run/{graph_run_id}")
@router.get("/traces/run/{graph_run_id}")
def graph_run_trace(graph_run_id: str) -> list[dict]:
    return get_graph_run_trace(graph_run_id)


@router.post("/api/approval-items/create")
@router.post("/api/approvals/create")
def create_approval(payload: ApprovalCreateRequest) -> dict:
    approval_id = create_pending_approval(
        payload.user_id,
        payload.application_id,
        payload.content_type,
        payload.original_content,
        payload.edited_content,
    )
    return {"id": approval_id, "status": "pending"}


@router.get("/api/approvals/pending/{user_id}")
@router.get("/api/approval-items/pending/{user_id}")
@router.get("/approvals/pending/{user_id}")
def pending_approvals(user_id: int) -> list[dict]:
    return get_pending_approvals(user_id)


@router.get("/api/approvals/history/{user_id}")
@router.get("/api/approval-items/history/{user_id}")
@router.get("/approvals/history/{user_id}")
def approval_history(user_id: int) -> list[dict]:
    return get_approval_history(user_id)


@router.post("/api/approvals/approve")
@router.post("/api/approval-items/approve")
@router.post("/approvals/approve")
def approve_item(payload: ApprovalActionRequest) -> dict:
    updated = approve_content(payload.approval_id, payload.edited_content, payload.reviewer_notes)
    if not updated:
        raise HTTPException(status_code=404, detail="Approval item not found.")
    return updated


@router.post("/api/approvals/reject")
@router.post("/api/approval-items/reject")
@router.post("/approvals/reject")
def reject_item(payload: ApprovalActionRequest) -> dict:
    updated = reject_content(payload.approval_id, payload.reviewer_notes)
    if not updated:
        raise HTTPException(status_code=404, detail="Approval item not found.")
    return updated


@router.post("/api/approvals/regenerate")
@router.post("/api/approval-items/regenerate")
@router.post("/approvals/regenerate")
def regenerate_item(payload: ApprovalActionRequest) -> dict:
    updated = request_regeneration(payload.approval_id, payload.reviewer_notes)
    if not updated:
        raise HTTPException(status_code=404, detail="Approval item not found.")
    return updated


@router.get("/api/deployment/status")
def deployment_status() -> dict:
    return {
        "service": "CareerPilot AI",
        "version": "4.0.0",
        "backend": "FastAPI",
        "frontend": "React + Vite",
        "database": "PostgreSQL" if DATABASE_DRIVER == "postgresql" else "SQLite",
        "postgres_ready": True,
        "rag_memory": "ChromaDB" if rag_memory.available else "Fallback mode",
        "llm_fallback": True,
        "docker_ready": True,
        "timestamp": datetime.utcnow().isoformat(timespec="seconds"),
    }
