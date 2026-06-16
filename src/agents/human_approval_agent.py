def run_human_approval_agent(state: dict) -> dict:
    if state.get("auto_approve"):
        bullets = (state.get("tailored_resume_bullets") or {}).get("tailored_bullets", [])
        cover_letter = (state.get("cover_letter") or {}).get("cover_letter", "")
        return {
            "approval_status": "approved",
            "approved_outputs": {
                "resume_bullets": bullets,
                "cover_letter": cover_letter,
            },
            "current_step": "human_approval_agent",
        }

    return {
        "approval_status": state.get("approval_status") or "pending",
        "approved_outputs": state.get("approved_outputs", {}),
        "current_step": "human_approval_agent",
    }
