from src.llm import call_llm_json, load_prompt


def _fallback_linkedin_optimization(state: dict) -> dict:
    text = state.get("linkedin_profile_text", "")
    job_title = state.get("job_title") or "AI/ML Engineer"
    resume_skills = (state.get("resume_analysis") or {}).get("skills", [])
    top_skills = resume_skills[:5] or ["Python", "Generative AI", "RAG", "FastAPI"]
    score = 70 if text.strip() else 35

    return {
        "new_headline": f"{job_title} | " + " | ".join(top_skills[:4]),
        "improved_about_section": (
            f"I build practical AI systems using {', '.join(top_skills[:4])}. "
            "My work focuses on turning business requirements into reliable AI workflows."
        ),
        "featured_projects_to_add": (state.get("resume_analysis") or {}).get("projects", [])[:4],
        "skills_to_reorder": top_skills,
        "experience_bullet_improvements": [
            "Use action verbs, job keywords, and evidence-backed project outcomes in each experience bullet."
        ],
        "profile_score": score,
    }


def run_linkedin_optimizer_agent(state: dict) -> dict:
    fallback = _fallback_linkedin_optimization(state)
    prompt = load_prompt("linkedin_optimizer_prompt.txt")
    output = call_llm_json(
        prompt,
        {
            "linkedin_profile_text": state.get("linkedin_profile_text", ""),
            "job_title": state.get("job_title", ""),
            "job_research": state.get("job_research", {}),
            "resume_analysis": state.get("resume_analysis", {}),
        },
        fallback=fallback,
    )
    return {"linkedin_optimization": output, "current_step": "linkedin_optimizer_agent"}
