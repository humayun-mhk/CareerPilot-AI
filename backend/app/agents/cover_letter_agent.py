from .llm import call_llm_json, load_prompt


def _fallback_cover_letter(state: dict) -> dict:
    company = state.get("company_name") or "your company"
    job_title = state.get("job_title") or "this role"
    evidence = state.get("evidence_report", {})
    strong = [skill for skill, data in evidence.items() if data.get("status") == "strong"][:5]
    avoided = [skill for skill, data in evidence.items() if data.get("status") != "strong"][:4]
    skill_text = ", ".join(strong) or "Python, AI workflows, and practical software development"

    return {
        "cover_letter": (
            "Dear Hiring Manager,\n\n"
            f"I am excited to apply for the {job_title} role at {company}. My background includes hands-on "
            f"work with {skill_text}, and I enjoy building practical AI systems that connect technical depth "
            "with useful business outcomes.\n\n"
            "I would welcome the opportunity to discuss how my project experience and learning mindset can "
            "support your team.\n\n"
            "Sincerely,\nYour Name"
        ),
        "used_evidence": strong,
        "avoided_claims": [
            f"{skill} was not strongly claimed because evidence was weak or missing."
            for skill in avoided
        ],
    }


def run_cover_letter_agent(state: dict) -> dict:
    fallback = _fallback_cover_letter(state)
    prompt = load_prompt("cover_letter_prompt.txt")
    output = call_llm_json(
        prompt,
        {
            "company_name": state.get("company_name", ""),
            "job_title": state.get("job_title", ""),
            "job_research": state.get("job_research", {}),
            "resume_analysis": state.get("resume_analysis", {}),
            "evidence_report": state.get("evidence_report", {}),
            "skill_gap_report": state.get("skill_gap_report", {}),
            "rag_context": state.get("rag_context", ""),
        },
        fallback=fallback,
    )
    return {"cover_letter": output, "current_step": "cover_letter_agent"}
