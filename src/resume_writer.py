import json
import os
import re

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


def _parse_bullets(content: str) -> list[str]:
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            parsed = parsed.get("bullets", [])
        if isinstance(parsed, list):
            return [str(item).strip(" -\n\t") for item in parsed if str(item).strip()]
    except json.JSONDecodeError:
        pass

    bullets = []
    for line in content.splitlines():
        cleaned = re.sub(r"^\s*[-*\d.)]+\s*", "", line).strip()
        if cleaned:
            bullets.append(cleaned)
    return bullets[:5]


def _fallback_resume_bullets(missing_skills: list[str]) -> list[str]:
    skill_phrase = ", ".join(missing_skills[:4]) if missing_skills else "job-relevant technologies"
    return [
        f"Built and improved Python-based applications using {skill_phrase} to solve business problems and support reliable user workflows.",
        "Designed clean data and API workflows that improved application performance, maintainability, and cross-functional collaboration.",
        "Translated project requirements into measurable technical deliverables, emphasizing automation, documentation, and production-ready code quality.",
    ]


def generate_resume_bullets(
    resume_text: str,
    job_description: str,
    missing_skills: list[str],
) -> list[str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        return _fallback_resume_bullets(missing_skills)

    client = OpenAI(api_key=api_key)
    prompt = f"""
Generate 3 to 5 improved resume bullets for this candidate, tailored to the job description.

Requirements:
- Professional, ATS-friendly, and achievement-focused.
- Do not invent employers, degrees, certifications, or exact metrics not supported by the resume.
- Naturally include relevant missing skills only when plausible.
- Return only a JSON array of strings.

Missing skills to consider:
{", ".join(missing_skills) if missing_skills else "None"}

Resume text:
\"\"\"
{resume_text[:9000]}
\"\"\"

Job description:
\"\"\"
{job_description[:9000]}
\"\"\"
"""

    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": "You write concise, truthful, ATS-friendly resume bullets and return valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )
        content = response.choices[0].message.content or "[]"
        bullets = _parse_bullets(content)
        return bullets[:5] if bullets else _fallback_resume_bullets(missing_skills)
    except Exception:
        return _fallback_resume_bullets(missing_skills)
