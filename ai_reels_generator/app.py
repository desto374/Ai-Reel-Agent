from __future__ import annotations

from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

from config.settings import get_settings
from services.job_manager import create_job, get_job
from services.pipeline import save_uploaded_video


load_dotenv()
app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    settings = get_settings()
    settings.ensure_directories()
    if request.method == "POST":
        uploads = [item for item in request.files.getlist("videos") if item and item.filename]
        if not uploads:
            return jsonify({"error": "Choose at least one .mp4 or .mov file."}), 400
        try:
            output_count = int(request.form.get("output_count", "5"))
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
    return jsonify(job.model_dump()), 200


if __name__ == "__main__":
    app.run(debug=True)
