import re

from .pdf_parser import extract_text_from_pdf


def parse_linkedin_text(text: str) -> str:
    text = text or ""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_linkedin_pdf(file_path: str) -> str:
    return parse_linkedin_text(extract_text_from_pdf(file_path))
