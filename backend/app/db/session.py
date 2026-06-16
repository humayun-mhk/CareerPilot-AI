import json
import sqlite3
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..core.config import DATABASE_DRIVER, DATABASE_PATH, DATABASE_URL, ENVIRONMENT

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    psycopg = None
    dict_row = None


def _is_postgres_url(database_url: str) -> bool:
    return database_url.startswith(
        ("postgresql://", "postgres://", "postgresql+psycopg://")
    )


def _ensure_neon_ssl(database_url: str) -> str:
    if not _is_postgres_url(database_url) or "sslmode=" in database_url:
        return database_url

    separator = "&" if "?" in database_url else "?"
    return f"{database_url}{separator}sslmode=require"


def _sqlalchemy_url() -> str:
    if not DATABASE_URL:
        if ENVIRONMENT == "production":
            raise RuntimeError(
                "DATABASE_URL must be set to a Neon PostgreSQL URL in production."
            )
        return f"sqlite:///{DATABASE_PATH.as_posix()}"

    if ENVIRONMENT == "production" and not _is_postgres_url(DATABASE_URL):
        raise RuntimeError(
            "Production must use Neon PostgreSQL. SQLite is only allowed locally."
        )

    url = _ensure_neon_ssl(DATABASE_URL)

    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)

    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)

    return url


SQLALCHEMY_DATABASE_URL = _sqlalchemy_url()
IS_POSTGRES = SQLALCHEMY_DATABASE_URL.startswith("postgresql+psycopg://")

# IMPORTANT:
# Do NOT put row_factory=dict_row here.
# SQLAlchemy needs a normal psycopg connection for its internal version check.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    connect_args={} if IS_POSTGRES else {"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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


class PostgresCursor:
    def __init__(self, cursor: Any, lastrowid: int | None = None) -> None:
        self._cursor = cursor
        self.lastrowid = lastrowid
        self.rowcount = cursor.rowcount

    def fetchone(self) -> Any:
        return self._cursor.fetchone()

    def fetchall(self) -> list[Any]:
        return self._cursor.fetchall()


class PostgresConnection:
    def __init__(self, database_url: str) -> None:
        if psycopg is None or dict_row is None:
            raise RuntimeError(
                "psycopg is required for PostgreSQL. Install requirements.txt first."
            )

        # SQLAlchemy pooled connection
        self._raw_conn = engine.raw_connection()

        # Actual psycopg connection behind SQLAlchemy proxy
        self._driver_conn = (
            getattr(self._raw_conn, "driver_connection", None)
            or getattr(self._raw_conn, "dbapi_connection", None)
            or self._raw_conn
        )

    def __enter__(self) -> "PostgresConnection":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> PostgresCursor:
        converted_sql = _to_postgres_sql(sql)
        returning_id = _needs_returning_id(converted_sql)

        if returning_id:
            converted_sql = f"{converted_sql.rstrip().rstrip(';')} RETURNING id"

        # Use dict_row only here, not in create_engine()
        cursor = self._driver_conn.cursor(row_factory=dict_row)
        cursor.execute(converted_sql, params)

        lastrowid = None

        if returning_id:
            row = cursor.fetchone()
            if row:
                lastrowid = int(row["id"])

        return PostgresCursor(cursor, lastrowid)

    def commit(self) -> None:
        self._raw_conn.commit()

    def rollback(self) -> None:
        self._raw_conn.rollback()

    def close(self) -> None:
        self._raw_conn.close()


def _to_postgres_sql(sql: str) -> str:
    return (
        sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        .replace("?", "%s")
    )


def _needs_returning_id(sql: str) -> bool:
    normalized = sql.lstrip().upper()
    return normalized.startswith("INSERT INTO") and " RETURNING " not in normalized


def get_connection() -> sqlite3.Connection | PostgresConnection:
    if DATABASE_DRIVER == "postgresql" or IS_POSTGRES:
        return PostgresConnection(SQLALCHEMY_DATABASE_URL)

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

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS github_evidence_scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                repositories_scanned INTEGER,
                report_json TEXT,
                created_at TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS github_repository_evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id INTEGER,
                user_id INTEGER,
                repo_name TEXT,
                repo_url TEXT,
                project_type TEXT,
                detected_skills_json TEXT,
                readme_summary TEXT,
                evidence_confidence REAL,
                created_at TEXT,
                FOREIGN KEY(scan_id) REFERENCES github_evidence_scans(id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS resume_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                resume_id INTEGER,
                job_id INTEGER,
                version_name TEXT,
                company TEXT,
                role TEXT,
                original_bullets TEXT,
                generated_bullets TEXT,
                approved_bullets TEXT,
                previous_match_score REAL,
                improved_match_score REAL,
                change_summary TEXT,
                approval_status TEXT,
                created_at TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS resume_exports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                resume_version_id INTEGER,
                job_id INTEGER,
                file_name TEXT,
                file_path TEXT,
                export_format TEXT,
                created_at TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluation_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                job_id INTEGER,
                application_id INTEGER,
                job_match_score INTEGER,
                skill_coverage_score INTEGER,
                evidence_confidence_score INTEGER,
                hallucination_risk_score INTEGER,
                ats_keyword_score INTEGER,
                cover_letter_personalization_score INTEGER,
                overall_quality_score INTEGER,
                issues_json TEXT,
                blocked_claims_json TEXT,
                recommendations_json TEXT,
                created_at TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_traces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                graph_run_id TEXT,
                user_id INTEGER,
                job_id INTEGER,
                agent_name TEXT,
                step_order INTEGER,
                input_summary TEXT,
                output_summary TEXT,
                input_json TEXT,
                output_json TEXT,
                tools_called_json TEXT,
                status TEXT,
                error_message TEXT,
                started_at TEXT,
                ended_at TEXT,
                duration_ms INTEGER
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS approval_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                application_id INTEGER,
                content_type TEXT,
                original_content TEXT,
                edited_content TEXT,
                approval_status TEXT,
                reviewer_notes TEXT,
                created_at TEXT,
                updated_at TEXT
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
            (
                _json(input_data),
                _json(output_data),
                output_data.get("approval_status", "pending"),
                None,
                now,
                now,
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def get_analysis_run(analysis_id: int) -> dict[str, Any] | None:
    init_db()

    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM analysis_runs WHERE id = ?",
            (analysis_id,),
        ).fetchone()

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
            (
                _json(output_data),
                approval_status,
                application_id,
                _now(),
                analysis_id,
            ),
        )
        conn.commit()


def save_application_record(
    state: dict[str, Any],
    approved_outputs: dict[str, Any],
) -> int:
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


def save_agent_run(
    application_id: int,
    step_name: str,
    input_json: dict[str, Any],
    output_json: Any,
) -> int:
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
                _json(input_json),
                _json(output_json),
                _now(),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def save_evidence_report(
    application_id: int,
    skill_name: str,
    details: dict[str, Any],
) -> int:
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
        total = conn.execute(
            "SELECT COUNT(*) AS count FROM applications"
        ).fetchone()["count"]

        average = conn.execute(
            "SELECT AVG(match_score) AS avg FROM applications"
        ).fetchone()["avg"] or 0

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

        nodes[skill_node] = {
            "id": skill_node,
            "label": row["skill_name"],
            "type": "skill",
        }

        edges.append(
            {
                "source": app_node,
                "target": skill_node,
                "confidence": row["confidence"],
                "status": row["status"],
            }
        )

    return {"nodes": list(nodes.values()), "edges": edges}


def save_github_evidence_scan(user_id: int, report: dict[str, Any]) -> int:
    init_db()

    now = _now()

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO github_evidence_scans (
                user_id, username, repositories_scanned, report_json, created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                report.get("username", ""),
                int(report.get("repositories_scanned", 0) or 0),
                _json(report),
                now,
            ),
        )

        scan_id = int(cursor.lastrowid)

        for project in report.get("projects", []):
            conn.execute(
                """
                INSERT INTO github_repository_evidence (
                    scan_id, user_id, repo_name, repo_url, project_type,
                    detected_skills_json, readme_summary, evidence_confidence, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scan_id,
                    user_id,
                    project.get("repo_name", ""),
                    project.get("repo_url", ""),
                    project.get("project_type", ""),
                    _json(project.get("detected_skills", [])),
                    project.get("readme_summary", ""),
                    float(project.get("evidence_confidence", 0) or 0),
                    now,
                ),
            )

        conn.commit()
        return scan_id


def get_latest_github_evidence(user_id: int) -> dict[str, Any] | None:
    init_db()

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM github_evidence_scans
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()

    if not row:
        return None

    data = dict(row)
    data["report"] = _loads(data.pop("report_json"), {})

    return data


def save_evaluation_report(report: dict[str, Any]) -> int:
    init_db()

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO evaluation_reports (
                user_id, job_id, application_id, job_match_score, skill_coverage_score,
                evidence_confidence_score, hallucination_risk_score, ats_keyword_score,
                cover_letter_personalization_score, overall_quality_score, issues_json,
                blocked_claims_json, recommendations_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report.get("user_id", 1),
                report.get("job_id"),
                report.get("application_id"),
                int(report.get("job_match_score", 0) or 0),
                int(report.get("skill_coverage_score", 0) or 0),
                int(report.get("evidence_confidence_score", 0) or 0),
                int(report.get("hallucination_risk_score", 0) or 0),
                int(report.get("ats_keyword_score", 0) or 0),
                int(report.get("cover_letter_personalization_score", 0) or 0),
                int(report.get("overall_quality_score", 0) or 0),
                _json(report.get("issues_found", [])),
                _json(report.get("blocked_claims", [])),
                _json(report.get("recommendations", [])),
                report.get("created_at") or _now(),
            ),
        )

        conn.commit()
        return int(cursor.lastrowid)


def get_evaluations(user_id: int) -> list[dict[str, Any]]:
    init_db()

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, user_id, job_id, application_id, job_match_score,
                   skill_coverage_score, evidence_confidence_score,
                   hallucination_risk_score, ats_keyword_score,
                   cover_letter_personalization_score, overall_quality_score,
                   created_at
            FROM evaluation_reports
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_evaluation_detail(evaluation_id: int) -> dict[str, Any] | None:
    init_db()

    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM evaluation_reports WHERE id = ?",
            (evaluation_id,),
        ).fetchone()

    if not row:
        return None

    data = dict(row)
    data["issues_found"] = _loads(data.pop("issues_json"), [])
    data["blocked_claims"] = _loads(data.pop("blocked_claims_json"), [])
    data["recommendations"] = _loads(data.pop("recommendations_json"), [])

    return data