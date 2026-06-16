from src.llm import call_llm_json, load_prompt
from src.tools.scoring_tool import weighted_match_score


def _fallback_skill_gap(state: dict) -> dict:
    score_data = weighted_match_score(state.get("job_research", {}), state.get("evidence_report", {}))
    weak = score_data["weak_skills"]
    missing = score_data["missing_skills"]
    plan = []
    for skill in weak[:3]:
        plan.append(f"Strengthen evidence for {skill} with a documented project or measurable result.")
    for skill in missing[:3]:
        plan.append(f"Build one portfolio project that demonstrates {skill}.")

    return {
        "overall_match": score_data["overall_match"],
        "strong_skills": score_data["strong_skills"],
        "weak_skills": weak,
        "missing_skills": missing,
        "priority_improvement_plan": plan,
    }


def run_skill_gap_agent(state: dict) -> dict:
    fallback = _fallback_skill_gap(state)
    prompt = load_prompt("skill_gap_prompt.txt")
    output = call_llm_json(
        prompt,
        {
            "job_research": state.get("job_research", {}),
            "resume_analysis": state.get("resume_analysis", {}),
            "evidence_report": state.get("evidence_report", {}),
            "fallback_score": fallback,
        },
        fallback=fallback,
    )
    return {"skill_gap_report": output, "current_step": "skill_gap_agent"}
