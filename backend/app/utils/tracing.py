import json
import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from ..db.session import get_connection, init_db


logger = logging.getLogger("careerpilot.tracing")


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="milliseconds")


def _json(data: Any) -> str:
    try:
        return json.dumps(data, ensure_ascii=False, default=str)
    except TypeError:
        return json.dumps(str(data))


def _summary(data: Any, max_length: int = 360) -> str:
    if isinstance(data, dict):
        keys = ", ".join(list(data.keys())[:12])
        text = f"dict keys: {keys}"
    elif isinstance(data, list):
        text = f"list length: {len(data)}"
    else:
        text = str(data)
    return text[:max_length]


def create_graph_run_id() -> str:
    return f"graph-{uuid4()}"


def start_agent_trace(
    graph_run_id: str,
    user_id: int,
    job_id: int | None,
    agent_name: str,
    step_order: int,
    input_data: dict[str, Any],
) -> int:
    init_db()
    started_at = _now()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO agent_traces (
                graph_run_id, user_id, job_id, agent_name, step_order,
                input_summary, input_json, tools_called_json, status, started_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                graph_run_id,
                user_id,
                job_id,
                agent_name,
                step_order,
                _summary(input_data),
                _json(input_data),
                _json([]),
                "running",
                started_at,
            ),
        )
        conn.commit()
        trace_id = int(cursor.lastrowid)
    logger.info("Agent started", extra={"agent_name": agent_name, "graph_run_id": graph_run_id})
    return trace_id


def end_agent_trace(trace_id: int, output_data: Any, status: str = "success", error_message: str = "") -> None:
    init_db()
    ended_at = _now()
    with get_connection() as conn:
        row = conn.execute("SELECT started_at FROM agent_traces WHERE id = ?", (trace_id,)).fetchone()
        duration_ms = 0
        if row and row["started_at"]:
            try:
                started = datetime.fromisoformat(row["started_at"])
                ended = datetime.fromisoformat(ended_at)
                duration_ms = int((ended - started).total_seconds() * 1000)
            except Exception:
                duration_ms = 0
        conn.execute(
            """
            UPDATE agent_traces
            SET output_summary = ?, output_json = ?, status = ?, error_message = ?,
                ended_at = ?, duration_ms = ?
            WHERE id = ?
            """,
            (_summary(output_data), _json(output_data), status, error_message, ended_at, duration_ms, trace_id),
        )
        conn.commit()
    if status == "success":
        logger.info("Agent finished", extra={"trace_id": trace_id, "duration_ms": duration_ms})
    else:
        logger.error("Agent failed", extra={"trace_id": trace_id, "error_message": error_message})


def log_tool_call(trace_id: int, tool_name: str, tool_input: Any, tool_output: Any) -> None:
    init_db()
    with get_connection() as conn:
        row = conn.execute("SELECT tools_called_json FROM agent_traces WHERE id = ?", (trace_id,)).fetchone()
        calls = []
        if row and row["tools_called_json"]:
            try:
                calls = json.loads(row["tools_called_json"])
            except json.JSONDecodeError:
                calls = []
        calls.append(
            {
                "tool_name": tool_name,
                "input_summary": _summary(tool_input),
                "output_summary": _summary(tool_output),
                "called_at": _now(),
            }
        )
        conn.execute("UPDATE agent_traces SET tools_called_json = ? WHERE id = ?", (_json(calls), trace_id))
        conn.commit()


def log_agent_error(trace_id: int, error_message: str) -> None:
    end_agent_trace(trace_id, {}, status="failed", error_message=error_message)


def get_agent_traces(user_id: int) -> list[dict[str, Any]]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM agent_traces
            WHERE user_id = ?
            ORDER BY started_at DESC, step_order ASC
            """,
            (user_id,),
        ).fetchall()
    return [_decode_trace(dict(row)) for row in rows]


def get_graph_run_trace(graph_run_id: str) -> list[dict[str, Any]]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM agent_traces
            WHERE graph_run_id = ?
            ORDER BY step_order ASC
            """,
            (graph_run_id,),
        ).fetchall()
    return [_decode_trace(dict(row)) for row in rows]


def _decode_trace(trace: dict[str, Any]) -> dict[str, Any]:
    for key in ["input_json", "output_json", "tools_called_json"]:
        try:
            trace[key.replace("_json", "")] = json.loads(trace.get(key) or "{}")
        except json.JSONDecodeError:
            trace[key.replace("_json", "")] = trace.get(key)
    return trace
