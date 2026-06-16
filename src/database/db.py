import json
import sqlite3
from datetime import datetime
from pathlib import Path

from src.database.models import ApplicationRecord


BASE_DIR = Path(__file__).resolve().parents[2]
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "careerpilot.db"


def get_connection() -> sqlite3.Connection:
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=OFF")
    conn.execute("PRAGMA synchronous=OFF")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT,
                job_title TEXT,
                job_link TEXT,
                job_description TEXT,
                match_score REAL,
                status TEXT,
                follow_up_date TEXT,
                approved_resume_bullets TEXT,
                approved_cover_letter TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER,
                step_name TEXT,
                input_json TEXT,
                output_json TEXT,
                created_at TEXT,
                FOREIGN KEY(application_id) REFERENCES applications(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS evidence_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER,
                skill_name TEXT,
                evidence_json TEXT,
                confidence REAL,
                status TEXT,
                created_at TEXT,
                FOREIGN KEY(application_id) REFERENCES applications(id)
            )
            """
        )
        conn.commit()


def save_application_record(record: dict) -> int:
    init_db()
    app = ApplicationRecord(**record)
    now = datetime.utcnow().isoformat(timespec="seconds")
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO applications (
                company_name, job_title, job_link, job_description, match_score,
                status, follow_up_date, approved_resume_bullets, approved_cover_letter,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                app.company_name,
                app.job_title,
                app.job_link,
                app.job_description,
                app.match_score,
                app.status,
                app.follow_up_date,
                json.dumps(app.approved_resume_bullets),
                app.approved_cover_letter,
                now,
                now,
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def save_agent_run(application_id: int, step_name: str, input_json: dict, output_json: dict) -> int:
    init_db()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO agent_runs (application_id, step_name, input_json, output_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                application_id,
                step_name,
                json.dumps(input_json),
                json.dumps(output_json),
                datetime.utcnow().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def save_evidence_report(application_id: int, skill_name: str, details: dict) -> int:
    init_db()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO evidence_reports (
                application_id, skill_name, evidence_json, confidence, status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                application_id,
                skill_name,
                json.dumps(details.get("evidence", [])),
                float(details.get("confidence", 0) or 0),
                details.get("status", "missing"),
                datetime.utcnow().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def get_all_applications() -> list[dict]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, company_name, job_title, job_link, match_score, status,
                   follow_up_date, created_at, updated_at
            FROM applications
            ORDER BY created_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def update_application_status(application_id: int, status: str) -> None:
    init_db()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE applications
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, datetime.utcnow().isoformat(timespec="seconds"), application_id),
        )
        conn.commit()
