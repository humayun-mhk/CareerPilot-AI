import re


def clean_job_description(job_description: str) -> str:
    text = job_description or ""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_job_input(
    job_title: str,
    company_name: str,
    job_link: str,
    job_description: str,
) -> dict[str, str]:
    return {
        "job_title": (job_title or "").strip(),
        "company_name": (company_name or "").strip(),
        "job_link": (job_link or "").strip(),
        "job_description": clean_job_description(job_description),
    }
