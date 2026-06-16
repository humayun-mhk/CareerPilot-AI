import re
from typing import BinaryIO

import fitz


def _clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_resume_text(pdf_file: BinaryIO) -> str:
    """Read an uploaded resume PDF with PyMuPDF and return clean text."""
    try:
        if hasattr(pdf_file, "seek"):
            pdf_file.seek(0)

        pdf_bytes = pdf_file.read()
        if not pdf_bytes:
            raise ValueError("The uploaded PDF file is empty.")

        with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
            page_text = [page.get_text("text") for page in document]

        return _clean_text("\n".join(page_text))
    except Exception as exc:
        raise ValueError(f"PDF parsing failed. Please upload a valid text-based PDF. Details: {exc}") from exc
