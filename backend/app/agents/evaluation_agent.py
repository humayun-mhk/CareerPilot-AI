import re
from datetime import datetime
from typing import Any


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def _coverage(required: list[str], text: str) -> int:
    if not required:
        return 70
    lower = text.lower()
    hits = sum(1 for skill in required if skill.lower() in lower)
    return round((hits / len(required)) * 100)


def _avg_evidence(evidence_report: dict[str, Any]) -> int:
    scores = [float(item.get("confidence", 0) or 0) for item in evidence_report.values() if isinstance(item, dict)]
    if not scores:
        return 30
    return round((sum(scores) / len(scores)) * 100)


def _blocked_claims(evidence_report: dict[str, Any]) -> list[str]:
    blocked = []
    for skill, details in evidence_report.items():
        if not isinstance(details, dict):
            continue
        confidence = float(details.get("confidence", 0) or 0)
        if confidence < 0.35:
            blocked.append(f"{skill} should not be claimed strongly because supporting evidence is weak.")
    return blocked[:8]


def _has_metrics(text: str) -> bool:
    return bool(re.search(r"\d+%|\$\d+|\b\d+x\b|\b\d+\+|\b\d+\s*(users|repos|projects|seconds|minutes)", text.lower()))


def run_evaluation_agent(state: dict) -> dict:
    job_research = state.get("job_research") or {}
    skill_gap = state.get("skill_gap_report") or {}
    evidence_report = state.get("evidence_report") or {}
    tailored = state.get("tailored_resume_bullets") or {}
    cover_letter = state.get("cover_letter") or {}

    bullets = _as_list(tailored.get("tailored_bullets"))
    cover_text = cover_letter.get("cover_letter", "") if isinstance(cover_letter, dict) else str(cover_letter)
    resume_text = "\n".join(bullets)
    combined_output = f"{resume_text}\n{cover_text}"

    required_skills = _as_list(job_research.get("must_have_skills")) + _as_list(job_research.get("good_to_have_skills"))
    ats_keywords = _as_list(job_research.get("keywords_for_ats")) or required_skills
    job_match_score = int(skill_gap.get("overall_match", 0) or _coverage(required_skills, combined_output))
    skill_coverage_score = _coverage(required_skills, combined_output)
    evidence_confidence_score = _avg_evidence(evidence_report)
    ats_keyword_score = _coverage(ats_keywords, combined_output)

    company = (state.get("company_name") or "").lower()
    role = (state.get("job_title") or "").lower()
    cover_lower = cover_text.lower()
    personalization_hits = int(bool(company and company in cover_lower)) + int(bool(role and role in cover_lower))
    cover_letter_personalization_score = min(100, 45 + personalization_hits * 20 + _coverage(required_skills[:5], cover_text) // 3)

    blocked_claims = _blocked_claims(evidence_report)
    hallucination_risk_score = min(95, len(blocked_claims) * 12 + max(0, 70 - evidence_confidence_score) // 2)

    issues = []
    recommendations = []
    if not _has_metrics(resume_text):
        issues.append("One or more resume bullets lack measurable impact.")
        recommendations.append("Add metrics such as latency reduction, accuracy, users, cost savings, or volume processed.")
    if cover_letter_personalization_score < 70:
        issues.append("Cover letter could be more specific to the company and role.")
        recommendations.append("Mention the company, role, and one job requirement naturally in the opening paragraph.")
    if evidence_confidence_score < 60:
        issues.append("Several claims have weak supporting evidence.")
        recommendations.append("Add GitHub README proof, portfolio links, or resume bullets for weak skills.")
    if hallucination_risk_score > 35:
        recommendations.append("Keep weak skills framed as exposure or learning rather than production expertise.")

    overall_quality_score = round(
        job_match_score * 0.24
        + skill_coverage_score * 0.18
        + evidence_confidence_score * 0.22
        + ats_keyword_score * 0.16
        + cover_letter_personalization_score * 0.12
        + (100 - hallucination_risk_score) * 0.08
    )

    report = {
        "user_id": int(state.get("user_id", 1) or 1),
        "job_id": state.get("job_id"),
        "application_id": (state.get("tracker_record") or {}).get("id"),
        "job_match_score": max(0, min(100, job_match_score)),
        "skill_coverage_score": max(0, min(100, skill_coverage_score)),
        "evidence_confidence_score": max(0, min(100, evidence_confidence_score)),
        "hallucination_risk_score": max(0, min(100, hallucination_risk_score)),
        "ats_keyword_score": max(0, min(100, ats_keyword_score)),
        "cover_letter_personalization_score": max(0, min(100, cover_letter_personalization_score)),
        "overall_quality_score": max(0, min(100, overall_quality_score)),
        "issues_found": issues,
        "blocked_claims": blocked_claims,
        "recommendations": recommendations,
        "created_at": datetime.utcnow().isoformat(timespec="seconds"),
    }
    return {"evaluation_report": report, "current_step": "evaluation_agent"}
