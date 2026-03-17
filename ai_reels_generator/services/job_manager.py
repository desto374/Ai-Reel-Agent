from __future__ import annotations

import threading
import uuid
from pathlib import Path
from typing import Any

from config.settings import Settings
from models.schemas import JobItem


_JOBS: dict[str, JobItem] = {}
_LOCK = threading.Lock()


def create_job(video_path: Path, settings: Settings, output_count: int, upload_to_drive: bool) -> JobItem:
    job = JobItem(
        job_id=f"job_{uuid.uuid4().hex[:10]}",
        filename=video_path.name,
        status="queued",
        stage="queued",
        progress=0,
    )
    with _LOCK:
        _JOBS[job.job_id] = job

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
        _update_job(job_id, status="completed", stage="completed", progress=100, result=result)
    except Exception as exc:
        _update_job(job_id, status="failed", stage="failed", error=str(exc), progress=100)
