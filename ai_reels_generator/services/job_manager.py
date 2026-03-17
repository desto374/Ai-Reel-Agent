from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import Settings
from models.schemas import JobItem
from services.debug_webhook import build_debug_payload, send_debug_to_n8n


_JOBS: dict[str, JobItem] = {}
_LOCK = threading.Lock()
_WATCHDOG_STARTED = False
_WATCHDOG_LOCK = threading.Lock()
WATCHDOG_INTERVAL_SECONDS = 30


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seconds_since(timestamp: str | None) -> float:
    if not timestamp:
        return 0.0
    try:
        updated = datetime.fromisoformat(timestamp)
    except ValueError:
        return 0.0
    return (datetime.now(timezone.utc) - updated).total_seconds()


def _start_watchdog(settings: Settings) -> None:
    global _WATCHDOG_STARTED
    with _WATCHDOG_LOCK:
        if _WATCHDOG_STARTED:
            return
        worker = threading.Thread(target=_watchdog_loop, args=(settings,), daemon=True)
        worker.start()
        _WATCHDOG_STARTED = True


def _watchdog_loop(settings: Settings) -> None:
    while True:
        stalled_reports: list[tuple[str, str, str]] = []
        with _LOCK:
            for job in _JOBS.values():
                if job.status != "running" or job.debug_reported:
                    continue
                stale_for = _seconds_since(job.updated_at)
                if stale_for < settings.job_stall_seconds:
                    continue
                warning = f"No progress update for {int(stale_for)}s while {job.stage}."
                job.warning = warning
                job.debug_reported = True
                stalled_reports.append((job.job_id, job.filename, warning))

        for job_id, filename, warning in stalled_reports:
            print(f"[job-watchdog] Job {job_id} appears stalled: {warning}")
            exc = RuntimeError(f"Job {job_id} stalled. {warning} Filename: {filename}")
            send_debug_to_n8n(
                build_debug_payload(
                    issue="CrewAI or pipeline failure",
                    exc=exc,
                    job_id=job_id,
                ),
                webhook_url=settings.debug_webhook_url,
            )

        threading.Event().wait(WATCHDOG_INTERVAL_SECONDS)


def create_job(video_path: Path, settings: Settings, output_count: int, upload_to_drive: bool) -> JobItem:
    now = _now_iso()
    job = JobItem(
        job_id=f"job_{uuid.uuid4().hex[:10]}",
        filename=video_path.name,
        status="queued",
        stage="queued",
        progress=0,
        created_at=now,
        updated_at=now,
    )
    with _LOCK:
        _JOBS[job.job_id] = job
    _start_watchdog(settings)

    worker = threading.Thread(
        target=_run_job,
        args=(job.job_id, video_path, settings, output_count, upload_to_drive),
        daemon=True,
    )
    worker.start()
    return job


def get_job(job_id: str) -> JobItem | None:
    with _LOCK:
        return _JOBS.get(job_id)


def _update_job(job_id: str, **changes) -> None:
    with _LOCK:
        job = _JOBS[job_id]
        for key, value in changes.items():
            setattr(job, key, value)
        job.updated_at = _now_iso()
        if changes.get("status") == "running":
            job.warning = None
            job.debug_reported = False


def _run_job(
    job_id: str,
    video_path: Path,
    settings: Settings,
    output_count: int,
    upload_to_drive: bool,
) -> None:
    try:
        from services.pipeline import run_pipeline

        def on_progress(stage: str, progress: int, **extra: Any) -> None:
            _update_job(job_id, status="running", stage=stage, progress=progress, **extra)

        _update_job(job_id, status="running", stage="queued", progress=0)
        result = run_pipeline(
            video_path=video_path,
            settings=settings,
            output_count=output_count,
            upload_to_drive=upload_to_drive,
            progress_callback=on_progress,
        )
        _update_job(job_id, status="completed", stage="completed", progress=100, result=result, warning=None)
    except Exception as exc:
        print(f"[job-manager] Job {job_id} failed: {exc}")
        send_debug_to_n8n(
            build_debug_payload(
                issue="CrewAI or pipeline failure",
                exc=exc,
                job_id=job_id,
            ),
            webhook_url=settings.debug_webhook_url,
        )
        _update_job(job_id, status="failed", stage="failed", error=str(exc), progress=100, warning=None)
