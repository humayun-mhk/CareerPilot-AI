from .llm import call_llm_json, load_prompt


def _fallback_resume_tailoring(state: dict) -> dict:
    job_title = state.get("job_title") or "target role"
    evidence = state.get("evidence_report", {})
    strong_skills = [skill for skill, data in evidence.items() if data.get("status") == "strong"]
    weak_skills = [skill for skill, data in evidence.items() if data.get("status") == "weak"]
    skills_text = ", ".join(strong_skills[:4]) or "Python and AI workflows"

    return {
        "tailored_bullets": [
            f"Built AI-focused applications for {job_title} requirements using {skills_text}, with emphasis on practical problem solving and clean implementation.",
            "Developed document-based AI workflows that connect user inputs, retrieval logic, and LLM APIs to generate useful responses.",
            "Improved project documentation and resume positioning by aligning technical work with job-specific ATS keywords and measurable responsibilities.",
        ],
        "keywords_added": strong_skills[:8],
        "honesty_notes": [
            f"{skill} had weak evidence, so it was described carefully and not overstated."
            for skill in weak_skills[:4]
        ],
    }


def run_resume_tailoring_agent(state: dict) -> dict:
    fallback = _fallback_resume_tailoring(state)
    prompt = load_prompt("resume_tailoring_prompt.txt")
    output = call_llm_json(
        prompt,
        {
            "resume_text": state.get("resume_text", ""),
            "job_research": state.get("job_research", {}),
            "evidence_report": state.get("evidence_report", {}),
            "skill_gap_report": state.get("skill_gap_report", {}),
            "rag_context": state.get("rag_context", ""),
        },
        fallback=fallback,
    )
    return {"tailored_resume_bullets": output, "current_step": "resume_tailoring_agent"}
