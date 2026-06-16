import json
import sqlite3
from datetime import date, datetime, timedelta
from typing import Any

from backend.config import DATABASE_PATH


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


def get_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_json TEXT NOT NULL,
                output_json TEXT NOT NULL,
                approval_status TEXT NOT NULL,
                application_id INTEGER,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY(application_id) REFERENCES applications(id)
            )
            """
        )
        conn.commit()


def save_analysis_run(input_data: dict[str, Any], output_data: dict[str, Any]) -> int:
    init_db()
    now = _now()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO analysis_runs (
                input_json, output_json, approval_status, application_id, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (_json(input_data), _json(output_data), output_data.get("approval_status", "pending"), None, now, now),
        )
        conn.commit()
        return int(cursor.lastrowid)


def get_analysis_run(analysis_id: int) -> dict[str, Any] | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM analysis_runs WHERE id = ?", (analysis_id,)).fetchone()
    if not row:
        return None
    data = dict(row)
    data["input"] = _loads(data.pop("input_json"), {})
    data["output"] = _loads(data.pop("output_json"), {})
    return data


def update_analysis_run(
    analysis_id: int,
    output_data: dict[str, Any],
    approval_status: str,
    application_id: int | None = None,
) -> None:
    init_db()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE analysis_runs
            SET output_json = ?, approval_status = ?, application_id = ?, updated_at = ?
            WHERE id = ?
            """,
            (_json(output_data), approval_status, application_id, _now(), analysis_id),
        )
        conn.commit()


def save_application_record(state: dict[str, Any], approved_outputs: dict[str, Any]) -> int:
    init_db()
    now = _now()
    follow_up_date = (date.today() + timedelta(days=7)).isoformat()
    match_score = (state.get("skill_gap_report") or {}).get("overall_match", 0)
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
                state.get("company_name", ""),
                state.get("job_title", ""),
                state.get("job_link", ""),
                state.get("job_description", ""),
                float(match_score or 0),
                "Ready to Apply",
                follow_up_date,
                _json(approved_outputs.get("resume_bullets", [])),
                approved_outputs.get("cover_letter", ""),
                now,
                now,
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def save_agent_run(application_id: int, step_name: str, input_json: dict[str, Any], output_json: Any) -> int:
    init_db()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO agent_runs (application_id, step_name, input_json, output_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (application_id, step_name, _json(input_json), _json(output_json), _now()),
        )
        conn.commit()
        return int(cursor.lastrowid)


def save_evidence_report(application_id: int, skill_name: str, details: dict[str, Any]) -> int:
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
                _json(details.get("evidence", [])),
                float(details.get("confidence", 0) or 0),
                details.get("status", "missing"),
                _now(),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def get_all_applications() -> list[dict[str, Any]]:
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


def update_application_status(application_id: int, status: str) -> bool:
    init_db()
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE applications SET status = ?, updated_at = ? WHERE id = ?",
            (status, _now(), application_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def get_analytics() -> dict[str, Any]:
    init_db()
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) AS count FROM applications").fetchone()["count"]
        average = conn.execute("SELECT AVG(match_score) AS avg FROM applications").fetchone()["avg"] or 0
        statuses = conn.execute(
            "SELECT status, COUNT(*) AS count FROM applications GROUP BY status ORDER BY count DESC"
        ).fetchall()
        recent = conn.execute(
            """
            SELECT id, company_name, job_title, match_score, status, created_at
            FROM applications
            ORDER BY created_at DESC
            LIMIT 5
            """
        ).fetchall()
    return {
        "total_applications": total,
        "average_match_score": round(float(average), 2),
        "status_counts": [dict(row) for row in statuses],
        "recent_applications": [dict(row) for row in recent],
    }


def get_evidence_graph(application_id: int | None = None) -> dict[str, list[dict[str, Any]]]:
    init_db()
    params: tuple[Any, ...] = ()
    where = ""
    if application_id is not None:
        where = "WHERE e.application_id = ?"
        params = (application_id,)

    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT e.application_id, e.skill_name, e.confidence, e.status,
                   a.company_name, a.job_title
            FROM evidence_reports e
            JOIN applications a ON a.id = e.application_id
            {where}
            ORDER BY e.application_id DESC, e.confidence DESC
            """,
            params,
        ).fetchall()

    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    for row in rows:
        app_node = f"application-{row['application_id']}"
        skill_node = f"skill-{row['skill_name']}"
        nodes[app_node] = {
            "id": app_node,
            "label": f"{row['company_name']} - {row['job_title']}".strip(" -"),
            "type": "application",
        }
        nodes[skill_node] = {"id": skill_node, "label": row["skill_name"], "type": "skill"}
        edges.append(
            {
                "source": app_node,
                "target": skill_node,
                "confidence": row["confidence"],
                "status": row["status"],
            }
        )
    return {"nodes": list(nodes.values()), "edges": edges}
