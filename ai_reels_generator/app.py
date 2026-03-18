from __future__ import annotations

import json
import threading
import time
import traceback
from pathlib import Path
from typing import Any

from flask import Flask, abort, jsonify, render_template, request, send_file, url_for
from dotenv import load_dotenv

from config.settings import get_settings
from services.job_manager import create_job, get_job
from services.pipeline import save_uploaded_video
from services.debug_webhook import build_event_payload, send_debug_to_n8n


load_dotenv()
app = Flask(__name__)
_STARTUP_LOCK = threading.Lock()
_STARTUP_DONE = False


def _json_preview(value: Any, limit: int = 1000) -> str:
    try:
        preview = json.dumps(value, default=str)
    except TypeError:
        preview = str(value)
    return preview[:limit]


def _filtered_headers(headers: dict[str, str]) -> dict[str, str]:
    allowed = {"content-type", "user-agent", "x-forwarded-for", "x-request-id"}
    return {key: value for key, value in headers.items() if key.lower() in allowed}


def _emit_startup_debug_once() -> None:
    global _STARTUP_DONE
    if _STARTUP_DONE:
        return
    with _STARTUP_LOCK:
        if _STARTUP_DONE:
            return
        settings = get_settings()
        settings.ensure_directories()
        print("[BOOT] Flask app initialized", flush=True)
        if not settings.openai_api_key:
            print("[BOOT][WARN] OPENAI_API_KEY is not set; CrewAI calls may fall back or fail.", flush=True)
            send_debug_to_n8n(
                build_event_payload(
                    "startup_warn",
                    data={"missing": "OPENAI_API_KEY"},
                    level="warn",
                ),
                webhook_url=settings.debug_webhook_url,
            )
        else:
            print("[BOOT] OPENAI_API_KEY detected.", flush=True)
            send_debug_to_n8n(
                build_event_payload(
                    "startup_ok",
                    data={"OPENAI_API_KEY_present": True},
                ),
                webhook_url=settings.debug_webhook_url,
            )
        _STARTUP_DONE = True


def _build_debug_crew(context: dict[str, Any]):
    from crewai import Agent, Crew, Task

    agent = Agent(
        role="Orchestrator",
        goal="Process the incoming request and produce a useful summary.",
        backstory="You are a helpful backend AI agent that processes webhook tasks.",
        verbose=True,
    )
    task = Task(
        description=(
            "Summarize the following request body and highlight notable keys.\n"
            f"{_json_preview(context.get('body', {}), limit=300)}\n"
            "Return a short actionable summary."
        ),
        agent=agent,
        expected_output="A concise summary of the request body.",
    )
    return Crew(agents=[agent], tasks=[task], verbose=True)


def _run_agent_debug_crew(context: dict[str, Any], webhook_url: str) -> None:
    print("[CREW] Building debug crew for /agent/run.", flush=True)
    send_debug_to_n8n(
        build_event_payload(
            "crew_started",
            data={"context_keys": sorted(context.keys())},
        ),
        webhook_url=webhook_url,
    )
    try:
        crew = _build_debug_crew(context)
        print("[CREW] Starting crew.kickoff() for /agent/run.", flush=True)
        try:
            result = crew.kickoff(inputs=context)
        except TypeError:
            result = crew.kickoff()
        result_text = "" if result is None else str(result)
        print("[CREW] crew.kickoff() completed for /agent/run.", flush=True)
        send_debug_to_n8n(
            build_event_payload(
                "crew_completed",
                data={
                    "result_preview": result_text[:1000],
                    "context_keys": sorted(context.keys()),
                },
            ),
            webhook_url=webhook_url,
        )
    except Exception as exc:
        error_trace = traceback.format_exc()
        print(f"[CREW][ERROR] {exc}\n{error_trace}", flush=True)
        send_debug_to_n8n(
            build_event_payload(
                "crew_failed",
                data={"traceback": error_trace},
                level="error",
                error=str(exc),
            ),
            webhook_url=webhook_url,
        )


def _is_downloadable_path(candidate: Path, settings) -> bool:
    resolved = candidate.resolve()
    allowed_roots = [
        settings.output_dir.resolve(),
        settings.uploads_dir.resolve(),
    ]
    return any(resolved.is_relative_to(root) for root in allowed_roots)


def _download_url(file_path: str | None) -> str | None:
    if not file_path:
        return None
    candidate = Path(file_path)
    if not candidate.exists():
        return None
    relative_path = candidate.resolve().relative_to(Path.cwd().resolve())
    return url_for("download_artifact", artifact_path=str(relative_path))


def _serialize_job(job):
    payload = job.model_dump()
    result = payload.get("result")
    if not result:
        return payload

    result["download_urls"] = {
        "transcript": _download_url(result.get("transcript_path")),
        "manifest": _download_url(result.get("manifest_path")),
    }

    for clip in result.get("clips", []):
        clip["download_urls"] = {
            "clip": _download_url(clip.get("clip_path")),
            "vertical": _download_url(clip.get("vertical_path")),
            "captioned": _download_url(clip.get("captioned_path")),
            "srt": _download_url(clip.get("srt_path")),
        }

    return payload


@app.before_request
def _before_request() -> None:
    _emit_startup_debug_once()


@app.route("/", methods=["GET", "POST"])
def index():
    settings = get_settings()
    settings.ensure_directories()
    if request.method == "POST":
        print("[RUN] Upload route hit", flush=True)
        send_debug_to_n8n(
            build_event_payload(
                "upload_request_received",
                data={
                    "path": request.path,
                    "method": request.method,
                    "headers": _filtered_headers(dict(request.headers)),
                    "file_count": len([item for item in request.files.getlist("videos") if item and item.filename]),
                },
            ),
            webhook_url=settings.debug_webhook_url,
        )
        uploads = [item for item in request.files.getlist("videos") if item and item.filename]
        if not uploads:
            return jsonify({"error": "Choose at least one .mp4 or .mov file."}), 400
        try:
            output_count = int(request.form.get("output_count", "3"))
            upload_to_drive = request.form.get("upload_to_drive", "true").lower() == "true"
            job_ids: list[str] = []
            for upload in uploads:
                saved_video = save_uploaded_video(upload, settings.uploads_dir)
                job = create_job(
                    video_path=saved_video,
                    settings=settings,
                    output_count=output_count,
                    upload_to_drive=upload_to_drive,
                )
                job_ids.append(job.job_id)
            print(f"[RUN] Scheduled {len(job_ids)} upload job(s): {job_ids}", flush=True)
            send_debug_to_n8n(
                build_event_payload(
                    "upload_jobs_scheduled",
                    data={"job_ids": job_ids, "output_count": output_count},
                ),
                webhook_url=settings.debug_webhook_url,
            )
            return jsonify({"job_ids": job_ids}), 202
        except Exception as exc:
            error_trace = traceback.format_exc()
            print(f"[RUN][ERROR] Upload route failed: {exc}\n{error_trace}", flush=True)
            send_debug_to_n8n(
                build_event_payload(
                    "upload_handler_failed",
                    data={"traceback": error_trace},
                    level="error",
                    error=str(exc),
                ),
                webhook_url=settings.debug_webhook_url,
            )
            return jsonify({"error": str(exc)}), 500
    print("[ROOT] Root route hit", flush=True)
    return render_template("index.html")


@app.get("/api/jobs/<job_id>")
def job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(_serialize_job(job)), 200


@app.get("/downloads/<path:artifact_path>")
def download_artifact(artifact_path: str):
    settings = get_settings()
    candidate = (Path.cwd() / artifact_path).resolve()
    if not candidate.exists() or not candidate.is_file():
        abort(404)
    if not _is_downloadable_path(candidate, settings):
        abort(403)
    return send_file(candidate, as_attachment=True, download_name=candidate.name)


@app.get("/health")
def health():
    settings = get_settings()
    print("[HEALTH] OK", flush=True)
    send_debug_to_n8n(
        build_event_payload("health_check", data={"status": "ok"}),
        webhook_url=settings.debug_webhook_url,
    )
    return jsonify({"status": "ok"}), 200


@app.post("/agent/run")
def run_agent():
    settings = get_settings()
    start_time = time.time()
    headers = dict(request.headers)
    raw_body = request.get_data(cache=True, as_text=True)

    try:
        body: Any = request.get_json(silent=True)
        if body is None:
            body = {"raw": raw_body}

        print("[RUN] /agent/run called", flush=True)
        print(f"[RUN] Headers: {_json_preview(headers)}", flush=True)
        print(f"[RUN] Body: {_json_preview(body)}", flush=True)

        send_debug_to_n8n(
            build_event_payload(
                "request_received",
                data={
                    "path": request.url,
                    "method": request.method,
                    "headers": _filtered_headers(headers),
                    "body_preview": _json_preview(body),
                },
            ),
            webhook_url=settings.debug_webhook_url,
        )

        context = {
            "headers": headers,
            "body": body,
            "received_at": int(start_time),
        }
        worker = threading.Thread(
            target=_run_agent_debug_crew,
            args=(context, settings.debug_webhook_url),
            daemon=True,
        )
        worker.start()
        latency_ms = int((time.time() - start_time) * 1000)
        print("[RUN] crew.kickoff() scheduled in background thread.", flush=True)
        send_debug_to_n8n(
            build_event_payload(
                "crew_scheduled",
                data={"scheduled": True, "latency_ms": latency_ms},
            ),
            webhook_url=settings.debug_webhook_url,
        )
        return (
            jsonify(
                {
                    "status": "scheduled",
                    "message": "Crew run has been scheduled.",
                    "latency_ms": latency_ms,
                }
            ),
            202,
        )
    except Exception as exc:
        error_trace = traceback.format_exc()
        print(f"[RUN][ERROR] {exc}\n{error_trace}", flush=True)
        send_debug_to_n8n(
            build_event_payload(
                "handler_failed",
                data={"traceback": error_trace},
                level="error",
                error=str(exc),
            ),
            webhook_url=settings.debug_webhook_url,
        )
        return jsonify({"status": "error", "error": str(exc)}), 500


if __name__ == "__main__":
    _emit_startup_debug_once()
    print("[BOOT] Starting local server on 0.0.0.0:8000", flush=True)
    app.run(host="0.0.0.0", port=8000, debug=True)
