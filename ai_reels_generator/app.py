from __future__ import annotations

from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request, send_file, url_for
from dotenv import load_dotenv

from config.settings import get_settings
from services.job_manager import create_job, get_job
from services.pipeline import save_uploaded_video


load_dotenv()
app = Flask(__name__)


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


@app.route("/", methods=["GET", "POST"])
def index():
    settings = get_settings()
    settings.ensure_directories()
    if request.method == "POST":
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
            return jsonify({"job_ids": job_ids}), 202
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500
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


if __name__ == "__main__":
    app.run(debug=True)
