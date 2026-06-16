from datetime import datetime
from typing import Any

from ..db.session import get_connection, init_db


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def _row(row: Any) -> dict[str, Any]:
    return dict(row) if row else {}


def create_pending_approval(
    user_id: int,
    application_id: int | None,
    content_type: str,
    original_content: str,
    edited_content: str = "",
) -> int:
    init_db()
    now = _now()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO approval_items (
                user_id, application_id, content_type, original_content, edited_content,
                approval_status, reviewer_notes, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                application_id,
                content_type,
                original_content,
                edited_content or original_content,
                "pending",
                "",
                now,
                now,
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def approve_content(approval_id: int, edited_content: str = "", reviewer_notes: str = "") -> dict[str, Any]:
    return _update_approval(approval_id, "edited" if edited_content else "approved", edited_content, reviewer_notes)


def reject_content(approval_id: int, reviewer_notes: str = "") -> dict[str, Any]:
    return _update_approval(approval_id, "rejected", "", reviewer_notes)


def request_regeneration(approval_id: int, reviewer_notes: str = "") -> dict[str, Any]:
    return _update_approval(approval_id, "regenerate_requested", "", reviewer_notes)


def _update_approval(
    approval_id: int,
    status: str,
    edited_content: str = "",
    reviewer_notes: str = "",
) -> dict[str, Any]:
    init_db()
    with get_connection() as conn:
        existing = conn.execute("SELECT * FROM approval_items WHERE id = ?", (approval_id,)).fetchone()
        if not existing:
            return {}
        final_content = edited_content or existing["edited_content"] or existing["original_content"]
        conn.execute(
            """
            UPDATE approval_items
            SET approval_status = ?, edited_content = ?, reviewer_notes = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, final_content, reviewer_notes, _now(), approval_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM approval_items WHERE id = ?", (approval_id,)).fetchone()
    return _row(row)


def get_pending_approvals(user_id: int) -> list[dict[str, Any]]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM approval_items
            WHERE user_id = ? AND approval_status = 'pending'
            ORDER BY created_at DESC
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_approval_history(user_id: int) -> list[dict[str, Any]]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM approval_items
            WHERE user_id = ?
            ORDER BY updated_at DESC
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]
