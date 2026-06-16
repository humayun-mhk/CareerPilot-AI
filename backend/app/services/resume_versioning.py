import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from ..core.config import EXPORT_DIR
from ..db.session import get_connection, init_db




def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def _loads(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _slug(value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip()).strip("_")
    return clean or "CareerPilot_Resume"


def create_resume_version(
    user_id: int,
    resume_id: int | None = None,
    job_id: int | None = None,
    version_name: str = "",
    company: str = "",
    role: str = "",
    original_bullets: list[str] | None = None,
    generated_bullets: list[str] | None = None,
    approved_bullets: list[str] | None = None,
    previous_match_score: float = 0,
    improved_match_score: float = 0,
    change_summary: str = "",
    approval_status: str = "pending",
) -> int:
    init_db()
    original_bullets = original_bullets or []
    generated_bullets = generated_bullets or []
    approved_bullets = approved_bullets or generated_bullets
    if not version_name:
        version_name = generate_resume_file_name(company, role).replace(".pdf", "")
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO resume_versions (
                user_id, resume_id, job_id, version_name, company, role,
                original_bullets, generated_bullets, approved_bullets,
                previous_match_score, improved_match_score, change_summary,
                approval_status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                resume_id,
                job_id,
                version_name,
                company,
                role,
                _json(original_bullets),
                _json(generated_bullets),
                _json(approved_bullets),
                float(previous_match_score or 0),
                float(improved_match_score or 0),
                change_summary,
                approval_status,
                _now(),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def compare_resume_versions(version_a_id: int, version_b_id: int) -> dict[str, Any]:
    first = get_resume_version_detail(version_a_id)
    second = get_resume_version_detail(version_b_id)
    if not first or not second:
        return {"error": "One or both resume versions were not found."}
    first_bullets = set(first.get("approved_bullets", []))
    second_bullets = set(second.get("approved_bullets", []))
    return {
        "version_a": first,
        "version_b": second,
        "added_bullets": sorted(second_bullets - first_bullets),
        "removed_bullets": sorted(first_bullets - second_bullets),
        "score_delta": round(float(second.get("improved_match_score", 0)) - float(first.get("improved_match_score", 0)), 2),
    }


def generate_resume_file_name(company: str, role: str) -> str:
    role_part = _slug(role or "AI_Engineer")
    company_part = _slug(company or "Target_Company")
    return f"Resume_for_{role_part}_{company_part}.pdf"


def export_resume_version_pdf(version_id: int, user_id: int = 1) -> dict[str, Any]:
    version = get_resume_version_detail(version_id)
    if not version:
        return {"error": "Resume version not found."}
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    file_name = generate_resume_file_name(version.get("company", ""), version.get("role", ""))
    path = EXPORT_DIR / file_name
    bullets = version.get("approved_bullets", []) or version.get("generated_bullets", [])
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        pdf = canvas.Canvas(str(path), pagesize=letter)
        width, height = letter
        y = height - 56
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(56, y, version.get("version_name") or "Tailored Resume Version")
        y -= 28
        pdf.setFont("Helvetica", 10)
        pdf.drawString(56, y, f"Role: {version.get('role', '')} | Company: {version.get('company', '')}")
        y -= 30
        for bullet in bullets:
            lines = _wrap_text(f"- {bullet}", 92)
            for line in lines:
                if y < 60:
                    pdf.showPage()
                    y = height - 56
                    pdf.setFont("Helvetica", 10)
                pdf.drawString(56, y, line)
                y -= 15
        pdf.save()
    except Exception:
        path.write_text("\n".join(bullets), encoding="utf-8")
    return _save_export_record(user_id, version_id, version.get("job_id"), file_name, path, "pdf")


def export_resume_version_txt(version_id: int, user_id: int = 1, export_format: str = "txt") -> dict[str, Any]:
    version = get_resume_version_detail(version_id)
    if not version:
        return {"error": "Resume version not found."}
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    extension = "md" if export_format == "markdown" else "txt"
    file_name = generate_resume_file_name(version.get("company", ""), version.get("role", "")).replace(".pdf", f".{extension}")
    path = EXPORT_DIR / file_name
    bullets = version.get("approved_bullets", []) or version.get("generated_bullets", [])
    content = [
        f"# {version.get('version_name') or 'Tailored Resume Version'}",
        "",
        f"Company: {version.get('company', '')}",
        f"Role: {version.get('role', '')}",
        "",
        "## Approved bullets",
        *[f"- {bullet}" for bullet in bullets],
        "",
        "## Change summary",
        version.get("change_summary", ""),
    ]
    path.write_text("\n".join(content), encoding="utf-8")
    return _save_export_record(user_id, version_id, version.get("job_id"), file_name, path, export_format)


def get_resume_versions(user_id: int) -> list[dict[str, Any]]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, user_id, resume_id, job_id, version_name, company, role,
                   previous_match_score, improved_match_score, change_summary,
                   approval_status, created_at
            FROM resume_versions
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_resume_version_detail(version_id: int) -> dict[str, Any] | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM resume_versions WHERE id = ?", (version_id,)).fetchone()
    if not row:
        return None
    data = dict(row)
    for key in ["original_bullets", "generated_bullets", "approved_bullets"]:
        data[key] = _loads(data.get(key), [])
    return data


def update_resume_version_approval(version_id: int, approved_bullets: list[str], approval_status: str = "approved") -> None:
    init_db()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE resume_versions
            SET approved_bullets = ?, approval_status = ?
            WHERE id = ?
            """,
            (_json(approved_bullets), approval_status, version_id),
        )
        conn.commit()


def _save_export_record(
    user_id: int,
    version_id: int,
    job_id: int | None,
    file_name: str,
    path: Path,
    export_format: str,
) -> dict[str, Any]:
    init_db()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO resume_exports (
                user_id, resume_version_id, job_id, file_name, file_path, export_format, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, version_id, job_id, file_name, str(path), export_format, _now()),
        )
        conn.commit()
        export_id = int(cursor.lastrowid)
    return {
        "id": export_id,
        "user_id": user_id,
        "resume_version_id": version_id,
        "job_id": job_id,
        "file_name": file_name,
        "file_path": str(path),
        "export_format": export_format,
        "created_at": _now(),
    }


def _wrap_text(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        if sum(len(item) for item in current) + len(current) + len(word) > width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines
