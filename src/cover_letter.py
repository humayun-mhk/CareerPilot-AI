import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


def _fallback_cover_letter(match_data: dict) -> str:
    strong_skills = ", ".join(match_data.get("strong_skills", [])[:5]) or "relevant technical skills"
    missing_skills = ", ".join(match_data.get("missing_skills", [])[:3])
    growth_sentence = (
        f"I am also actively strengthening my experience with {missing_skills}."
        if missing_skills
        else "I am confident my background aligns well with the role."
    )

    return (
        "Dear Hiring Manager,\n\n"
        "I am excited to apply for this role. My background includes hands-on experience with "
        f"{strong_skills}, and I enjoy building practical, reliable solutions that connect technical work "
        f"to business outcomes. {growth_sentence}\n\n"
        "I would welcome the opportunity to discuss how my experience can support your team.\n\n"
        "Sincerely,\n"
        "Your Name"
    )


def generate_cover_letter(
    resume_text: str,
    job_description: str,
    match_data: dict,
) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        return _fallback_cover_letter(match_data)

    client = OpenAI(api_key=api_key)
    prompt = f"""
Write a concise customized cover letter for this candidate and job.

Requirements:
- 3 to 5 short paragraphs.
- Professional and specific.
- Do not invent personal details, employers, exact years, or metrics.
- Mention strongest aligned skills when useful.
- Address missing skills with a growth mindset only if needed.

Match data:
{match_data}

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
                    "content": "You write concise, truthful, customized cover letters.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
        )
        content = response.choices[0].message.content
        return content.strip() if content else _fallback_cover_letter(match_data)
    except Exception:
        return _fallback_cover_letter(match_data)
