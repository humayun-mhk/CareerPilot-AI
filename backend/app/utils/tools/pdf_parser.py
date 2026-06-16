import re
from pathlib import Path

import fitz


def _clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text_from_pdf(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    try:
        with fitz.open(path) as document:
            return _clean_text("\n".join(page.get_text("text") for page in document))
    except Exception as exc:
        raise ValueError(f"Invalid or unreadable PDF: {exc}") from exc


def extract_text_from_uploaded_pdf(uploaded_file) -> str:
    try:
        uploaded_file.seek(0)
        with fitz.open(stream=uploaded_file.read(), filetype="pdf") as document:
            return _clean_text("\n".join(page.get_text("text") for page in document))
    except Exception as exc:
        raise ValueError(f"Invalid or unreadable uploaded PDF: {exc}") from exc
