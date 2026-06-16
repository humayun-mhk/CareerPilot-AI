from .llm import call_llm_json, load_prompt


def _fallback_projects(state: dict) -> dict:
    gap = state.get("skill_gap_report", {})
    target_skills = (gap.get("missing_skills", []) + gap.get("weak_skills", []))[:5]
    projects = []
    for skill in target_skills:
        projects.append(
            {
                "project_name": f"{skill} Proof Project",
                "missing_skill_solved": skill,
                "tech_stack": ["Python", "Streamlit", "FastAPI", "OpenAI"],
                "why_it_helps": f"Creates concrete evidence that the candidate can use {skill} in a practical workflow.",
                "resume_bullet_after_completion": f"Built a portfolio project demonstrating {skill} with Python, APIs, documentation, and user-facing outputs.",
            }
        )
    return {"recommended_projects": projects}


def run_project_recommender_agent(state: dict) -> dict:
    fallback = _fallback_projects(state)
    prompt = load_prompt("project_recommender_prompt.txt")
    output = call_llm_json(
        prompt,
        {
            "skill_gap_report": state.get("skill_gap_report", {}),
            "job_research": state.get("job_research", {}),
            "resume_analysis": state.get("resume_analysis", {}),
        },
        fallback=fallback,
    )
    return {"recommended_projects": output, "current_step": "project_recommender_agent"}
