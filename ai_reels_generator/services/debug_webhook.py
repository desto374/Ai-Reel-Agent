from __future__ import annotations

import json
import os
import traceback
from pathlib import Path
from typing import Any

import requests


DEFAULT_DEBUG_WEBHOOK_URL = "https://desto374.app.n8n.cloud/webhook/auto-debug"


def _extract_code_snippet_from_traceback(exc: BaseException, max_lines: int = 12) -> str:
    tb_frames = traceback.extract_tb(exc.__traceback__)
    if not tb_frames:
        return ""

    frame = tb_frames[-1]
    file_path = Path(frame.filename)
    if not file_path.exists():
        return ""

    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""

    line_number = max(1, frame.lineno)
    start = max(1, line_number - max_lines // 2)
    end = min(len(lines), line_number + max_lines // 2)
    snippet_lines: list[str] = []
    for index in range(start, end + 1):
        marker = ">>" if index == line_number else "  "
        snippet_lines.append(f"{marker} {index}: {lines[index - 1]}")
    return "\n".join(snippet_lines)


def build_debug_payload(
    issue: str,
    exc: BaseException,
    job_id: str | None = None,
    service: str = "render-backend",
) -> dict[str, Any]:
    error_message = str(exc) or exc.__class__.__name__
    trace = traceback.format_exc()
    code_snippet = _extract_code_snippet_from_traceback(exc)
    logs = trace.strip()
    if code_snippet:
        logs = f"{logs}\n\nCode snippet:\n{code_snippet}"

    return {
        "issue": issue,
        "error": error_message,
        "logs": logs,
        "job_id": job_id or "",
        "service": service,
    }


def build_event_payload(
    event: str,
    data: dict[str, Any] | None = None,
    *,
    level: str = "info",
    error: str | None = None,
    service: str = "render-backend",
) -> dict[str, Any]:
    return {
        "event": event,
        "level": level,
        "service": service,
        "data": data or {},
        "error": error,
    }


def _coerce_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _coerce_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_coerce_jsonable(item) for item in value]
    if hasattr(value, "model_dump"):
        return _coerce_jsonable(value.model_dump())
    if hasattr(value, "dict"):
        return _coerce_jsonable(value.dict())
    return str(value)


def send_debug_to_n8n(data: dict[str, Any], webhook_url: str | None = None) -> None:
    target_url = webhook_url or os.getenv("N8N_WEBHOOK_URL") or os.getenv("DEBUG_WEBHOOK_URL") or DEFAULT_DEBUG_WEBHOOK_URL
    payload = _coerce_jsonable(data)
    try:
        print(f"[debug-webhook] Sending debug payload to {target_url}")
        response = requests.post(target_url, json=payload, timeout=5)
        print(f"[debug-webhook] Sent debug payload to n8n with status {response.status_code}")
    except Exception as webhook_exc:
        print(f"[debug-webhook] Failed to send payload to n8n: {webhook_exc}")
        fallback_payload = json.dumps(payload, default=str)
        print(f"[debug-webhook] Fallback payload: {fallback_payload}")
