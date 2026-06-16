import re

from .llm import call_llm_json, load_prompt
from .skill_extractor import fallback_skill_extraction


def _interesting_lines(text: str, keywords: list[str], limit: int = 6) -> list[str]:
    lines = []
    for line in text.splitlines():
        cleaned = line.strip(" -\t")
        if len(cleaned) < 8:
            continue
        if any(keyword in cleaned.lower() for keyword in keywords):
            lines.append(cleaned)
    return lines[:limit]


def _fallback_resume_analysis(resume_text: str) -> dict:
    skills = fallback_skill_extraction(resume_text)
    projects = _interesting_lines(resume_text, ["project", "built", "developed", "rag", "chatbot"])
    experience = _interesting_lines(resume_text, ["intern", "engineer", "developer", "experience", "worked"])
    education = _interesting_lines(resume_text, ["bs", "bachelor", "master", "university", "degree"])
    weak_points = []
    if not re.search(r"\d+%|\$\d+|\b\d+x\b|\b\d+\+", resume_text.lower()):
        weak_points.append("Few measurable outcomes or metrics found.")
    if "deploy" not in resume_text.lower():
        weak_points.append("Deployment details are not clearly evidenced.")

    strength = min(95, 35 + len(skills) * 4 + len(projects) * 5 + len(experience) * 3)
    return {
        "skills": skills,
        "projects": projects,
        "experience": experience,
        "education": education,
        "weak_points": weak_points,
        "missing_keywords": [],
        "resume_strength": strength,
    }


def run_resume_analyzer_agent(state: dict) -> dict:
    resume_text = state.get("resume_text", "")
    fallback = _fallback_resume_analysis(resume_text)
    prompt = load_prompt("resume_analyzer_prompt.txt")
    output = call_llm_json(prompt, {"resume_text": resume_text}, fallback=fallback)
    return {"resume_analysis": output, "current_step": "resume_analyzer_agent"}
