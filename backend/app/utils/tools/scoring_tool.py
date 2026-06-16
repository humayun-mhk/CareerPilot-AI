def classify_skill_evidence(confidence: float) -> str:
    if confidence >= 0.75:
        return "strong"
    if confidence >= 0.35:
        return "weak"
    return "missing"


def weighted_match_score(job_research: dict, evidence_report: dict) -> dict:
    must_have = job_research.get("must_have_skills", []) or []
    good_to_have = job_research.get("good_to_have_skills", []) or []
    weighted_skills = [(skill, 2.0) for skill in must_have] + [(skill, 1.0) for skill in good_to_have]

    possible = sum(weight for _, weight in weighted_skills)
    earned = 0.0
    strong_skills = []
    weak_skills = []
    missing_skills = []

    for skill, weight in weighted_skills:
        details = evidence_report.get(skill, {})
        status = details.get("status") or classify_skill_evidence(float(details.get("confidence", 0) or 0))
        if status == "strong":
            earned += weight
            strong_skills.append(skill)
        elif status == "weak":
            earned += weight * 0.5
            weak_skills.append(skill)
        else:
            missing_skills.append(skill)

    overall_match = round((earned / possible) * 100, 2) if possible else 0
    return {
        "overall_match": overall_match,
        "strong_skills": list(dict.fromkeys(strong_skills)),
        "weak_skills": list(dict.fromkeys(weak_skills)),
        "missing_skills": list(dict.fromkeys(missing_skills)),
    }
