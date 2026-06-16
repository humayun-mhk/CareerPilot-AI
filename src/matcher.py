from typing import Iterable


def _normalize_skill(skill: str) -> str:
    return " ".join(str(skill).strip().lower().split())


def _dedupe(skills: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for skill in skills:
        cleaned = str(skill).strip()
        if not cleaned:
            continue

        key = _normalize_skill(cleaned)
        if key not in seen:
            seen.add(key)
            result.append(cleaned)

    return result


def calculate_match_score(resume_skills: list[str], job_skills: list[str]) -> dict:
    unique_resume_skills = _dedupe(resume_skills)
    unique_job_skills = _dedupe(job_skills)
    resume_lookup = {_normalize_skill(skill): skill for skill in unique_resume_skills}

    strong_skills = [
        job_skill
        for job_skill in unique_job_skills
        if _normalize_skill(job_skill) in resume_lookup
    ]
    missing_skills = [
        job_skill
        for job_skill in unique_job_skills
        if _normalize_skill(job_skill) not in resume_lookup
    ]

    if not unique_job_skills:
        match_percentage = 0
    else:
        match_percentage = round((len(strong_skills) / len(unique_job_skills)) * 100, 2)

    return {
        "match_percentage": match_percentage,
        "strong_skills": strong_skills,
        "missing_skills": missing_skills,
    }
