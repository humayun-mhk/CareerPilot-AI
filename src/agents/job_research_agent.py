from src.llm import call_llm_json, load_prompt
from src.skill_extractor import fallback_skill_extraction


def _detect_seniority(job_title: str, job_description: str) -> str:
    text = f"{job_title} {job_description}".lower()
    if any(word in text for word in ["senior", "lead", "principal", "staff"]):
        return "Senior"
    if any(word in text for word in ["junior", "entry", "intern", "graduate"]):
        return "Junior"
    return "Junior/Mid-level" if any(word in text for word in ["0-2", "1-3", "mid"]) else "Mid-level"


def _fallback_job_research(state: dict) -> dict:
    job_description = state.get("job_description", "")
    skills = fallback_skill_extraction(job_description)
    must_have = skills[: max(1, min(6, len(skills)))]
    good_to_have = [skill for skill in skills if skill not in must_have]
    responsibilities = [
        line.strip(" -")
        for line in job_description.splitlines()
        if len(line.strip()) > 25
    ][:6]

    return {
        "must_have_skills": must_have,
        "good_to_have_skills": good_to_have[:8],
        "tools": skills[:8],
        "responsibilities": responsibilities,
        "seniority": _detect_seniority(state.get("job_title", ""), job_description),
        "job_category": state.get("job_title") or "AI Engineer",
        "keywords_for_ats": skills[:10],
    }


def run_job_research_agent(state: dict) -> dict:
    fallback = _fallback_job_research(state)
    prompt = load_prompt("job_research_prompt.txt")
    output = call_llm_json(
        prompt,
        {
            "job_title": state.get("job_title", ""),
            "company_name": state.get("company_name", ""),
            "job_link": state.get("job_link", ""),
            "job_description": state.get("job_description", ""),
        },
        fallback=fallback,
    )
    return {"job_research": output, "current_step": "job_research_agent"}
