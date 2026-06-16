import re

from .llm import call_llm_json, load_prompt
from ..utils.tools.scoring_tool import classify_skill_evidence


def _skill_pattern(skill: str) -> re.Pattern:
    escaped = re.escape(skill.lower()).replace("\\ ", r"\s+")
    return re.compile(r"(?<![a-z0-9+#.-])" + escaped + r"(?![a-z0-9+#.-])")


def _source_hits(skill: str, sources: dict[str, str]) -> list[str]:
    pattern = _skill_pattern(skill)
    hits = []
    for source_name, text in sources.items():
        if text and pattern.search(text.lower()):
            hits.append(f"Mentioned in {source_name}")
    return hits


def _fallback_evidence_report(state: dict) -> dict:
    job_research = state.get("job_research") or {}
    resume_analysis = state.get("resume_analysis") or {}
    skills = []
    for key in ["must_have_skills", "good_to_have_skills"]:
        skills.extend(job_research.get(key, []))
    skills.extend(resume_analysis.get("skills", []))

    sources = {
        "resume": state.get("resume_text", ""),
        "linkedin": state.get("linkedin_profile_text", ""),
        "github": state.get("github_evidence_text", ""),
        "github scan": "\n".join(
            f"{skill}: {', '.join(details.get('repos', []))}"
            for skill, details in ((state.get("github_evidence_report") or {}).get("skill_evidence_summary", {})).items()
        ),
        "portfolio": state.get("portfolio_evidence_text", ""),
        "career memory": state.get("rag_context", ""),
    }

    report = {}
    for skill in dict.fromkeys(skills):
        hits = _source_hits(skill, sources)
        confidence = 0.0
        if len(hits) >= 2:
            confidence = 0.85
        elif hits and "Mentioned in resume" in hits:
            confidence = 0.65
        elif hits:
            confidence = 0.45

        report[skill] = {
            "evidence": hits,
            "confidence": confidence,
            "status": classify_skill_evidence(confidence),
        }
    return report


def _normalize_report(report: dict) -> dict:
    normalized = {}
    for skill, details in (report or {}).items():
        if not isinstance(details, dict):
            continue
        confidence = float(details.get("confidence", 0) or 0)
        confidence = max(0.0, min(1.0, confidence))
        evidence = details.get("evidence", [])
        if not evidence:
            confidence = 0.0
        normalized[skill] = {
            "evidence": evidence if isinstance(evidence, list) else [str(evidence)],
            "confidence": confidence,
            "status": classify_skill_evidence(confidence),
        }
    return normalized


def run_evidence_verification_agent(state: dict) -> dict:
    fallback = _fallback_evidence_report(state)
    prompt = load_prompt("evidence_prompt.txt")
    llm_output = call_llm_json(
        prompt,
        {
            "resume_analysis": state.get("resume_analysis", {}),
            "resume_text": state.get("resume_text", ""),
            "linkedin_profile_text": state.get("linkedin_profile_text", ""),
            "github_evidence_text": state.get("github_evidence_text", ""),
            "github_evidence_report": state.get("github_evidence_report", {}),
            "portfolio_evidence_text": state.get("portfolio_evidence_text", ""),
            "rag_context": state.get("rag_context", ""),
            "job_research": state.get("job_research", {}),
        },
        fallback=fallback,
    )
    return {"evidence_report": _normalize_report(llm_output), "current_step": "evidence_verification_agent"}
