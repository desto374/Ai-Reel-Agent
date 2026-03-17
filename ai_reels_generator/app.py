from __future__ import annotations

from flask import Flask, jsonify, render_template_string, request
from dotenv import load_dotenv

from config.settings import get_settings
from services.job_manager import create_job, get_job
from services.pipeline import save_uploaded_video


load_dotenv()
app = Flask(__name__)


HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AI Reels Generator</title>
    <style>
      :root {
        --bg: #f4efe7;
        --panel: #fffaf2;
        --ink: #1f2937;
        --accent: #bb4d00;
        --muted: #6b7280;
        --border: #e7dcc9;
      }
      body {
        margin: 0;
        font-family: Georgia, "Times New Roman", serif;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, rgba(187,77,0,.12), transparent 35%),
          linear-gradient(180deg, #f8f4ed, var(--bg));
      }
      .wrap {
        max-width: 920px;
        margin: 48px auto;
        padding: 24px;
      }
      .card {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 28px;
        box-shadow: 0 20px 40px rgba(44, 24, 0, 0.08);
      }
      h1 { margin-top: 0; font-size: 2.4rem; }
      p { color: var(--muted); line-height: 1.5; }
      form { display: grid; gap: 16px; margin-top: 24px; }
      label { font-weight: 600; }
      input, button {
        font: inherit;
        padding: 12px 14px;
        border-radius: 12px;
        border: 1px solid var(--border);
      }
      button {
        background: var(--accent);
        color: white;
        border: none;
        cursor: pointer;
      }
      button:disabled {
        cursor: wait;
        opacity: .65;
      }
      .dropzone {
        border: 2px dashed var(--border);
        border-radius: 16px;
        padding: 28px;
        background: rgba(255,255,255,.65);
        text-align: center;
        transition: border-color .2s ease, transform .2s ease, background .2s ease;
      }
      .dropzone.dragover {
        border-color: var(--accent);
        background: rgba(187,77,0,.06);
        transform: scale(1.01);
      }
      .hidden-input {
        display: none;
      }
      .browse-link {
        color: var(--accent);
        font-weight: 700;
        cursor: pointer;
      }
      .file-list {
        display: grid;
        gap: 10px;
        margin-top: 12px;
      }
      .file-pill {
        background: #fff;
        border: 1px solid var(--border);
        border-radius: 999px;
        padding: 8px 12px;
        font-size: .95rem;
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 16px;
      }
      .status {
        margin-top: 20px;
        display: none;
      }
      .progress {
        width: 100%;
        height: 12px;
        background: #eadfce;
        border-radius: 999px;
        overflow: hidden;
      }
      .progress-bar {
        width: 0%;
        height: 100%;
        background: linear-gradient(90deg, #bb4d00, #e47b2c);
        transition: width .15s ease;
      }
      .status-text {
        margin-top: 8px;
        color: var(--muted);
        font-size: .95rem;
      }
      .error {
        color: #8b1e1e;
        margin-bottom: 16px;
      }
      .result {
        margin-top: 28px;
        padding-top: 20px;
        border-top: 1px solid var(--border);
      }
      .clip {
        margin-top: 14px;
        padding: 14px;
        background: #fff;
        border: 1px solid var(--border);
        border-radius: 12px;
      }
      .job {
        margin-top: 20px;
        padding-top: 20px;
        border-top: 1px solid var(--border);
      }
      code { background: #f5eadb; padding: 2px 6px; border-radius: 6px; }
      @media (max-width: 760px) {
        .wrap { margin: 20px auto; padding: 16px; }
        .card { padding: 20px; }
        .grid { grid-template-columns: 1fr; }
        h1 { font-size: 2rem; }
      }
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="card">
        <h1>AI Reels Generator</h1>
        <p>Drop one or more long-form <code>.mp4</code> or <code>.mov</code> videos here. The pipeline will transcribe them, pick strong moments, render vertical clips, burn captions, and upload exports to Google Drive when configured.</p>
        <div id="errorBox" class="error" style="display:none;"></div>
        <form id="uploadForm" method="post" enctype="multipart/form-data">
          <div class="dropzone" id="dropzone">
            <input id="videos" class="hidden-input" type="file" name="videos" accept=".mp4,.mov" multiple required>
            <strong>Drag and drop videos here</strong>
            <p>or <span class="browse-link" id="browseLink">browse from your computer</span></p>
            <p>Supported formats: <code>.mp4</code>, <code>.mov</code></p>
            <div id="fileList" class="file-list"></div>
          </div>
          <div class="grid">
            <div>
              <label for="output_count">How many clips per video</label><br>
              <input id="output_count" type="number" name="output_count" min="1" max="10" value="5">
            </div>
            <div>
              <label for="upload_to_drive">Delivery</label><br>
              <select id="upload_to_drive" name="upload_to_drive">
                <option value="true">Upload to Google Drive</option>
                <option value="false">Save locally only</option>
              </select>
            </div>
          </div>
          <button id="submitButton" type="submit">Generate Reels</button>
        </form>
        <div id="statusBox" class="status">
          <div class="progress"><div id="progressBar" class="progress-bar"></div></div>
          <div id="statusText" class="status-text">Uploading...</div>
        </div>
        <div id="results" class="result" style="display:none;"></div>
      </div>
    </div>
    <script>
      const form = document.getElementById('uploadForm');
      const input = document.getElementById('videos');
      const dropzone = document.getElementById('dropzone');
      const browseLink = document.getElementById('browseLink');
      const fileList = document.getElementById('fileList');
      const errorBox = document.getElementById('errorBox');
      const results = document.getElementById('results');
      const statusBox = document.getElementById('statusBox');
      const statusText = document.getElementById('statusText');
      const progressBar = document.getElementById('progressBar');
      const submitButton = document.getElementById('submitButton');
      let activeJobIds = [];

      browseLink.addEventListener('click', () => input.click());
      input.addEventListener('change', renderFiles);

      ['dragenter', 'dragover'].forEach((eventName) => {
        dropzone.addEventListener(eventName, (event) => {
          event.preventDefault();
          dropzone.classList.add('dragover');
        });
      });

      ['dragleave', 'drop'].forEach((eventName) => {
        dropzone.addEventListener(eventName, (event) => {
          event.preventDefault();
          dropzone.classList.remove('dragover');
        });
      });

      dropzone.addEventListener('drop', (event) => {
        input.files = event.dataTransfer.files;
        renderFiles();
      });

      function renderFiles() {
        fileList.innerHTML = '';
        Array.from(input.files || []).forEach((file) => {
          const item = document.createElement('div');
          item.className = 'file-pill';
          item.textContent = `${file.name} (${Math.round(file.size / 1024 / 1024 * 10) / 10} MB)`;
          fileList.appendChild(item);
        });
      }

      function showError(message) {
        errorBox.style.display = 'block';
        errorBox.textContent = message;
      }

      function clearError() {
        errorBox.style.display = 'none';
        errorBox.textContent = '';
      }

      function renderResults(payload) {
        results.style.display = 'block';
        results.innerHTML = '';
        const jobs = payload.results || [];
        jobs.forEach((job) => {
          const section = document.createElement('div');
          section.className = 'job';
          section.innerHTML = `
            <p><strong>Video:</strong> ${job.source_video}</p>
            <p><strong>Transcript:</strong> ${job.transcript_path}</p>
            <p><strong>Manifest:</strong> ${job.manifest_path}</p>
          `;
          (job.clips || []).forEach((clip) => {
            const item = document.createElement('div');
            item.className = 'clip';
            item.innerHTML = `
              <strong>${clip.title}</strong><br>
              Source: ${clip.source_start}s to ${clip.source_end}s<br>
              Captioned file: ${clip.captioned_path}<br>
              ${clip.drive_link ? `Drive: <a href="${clip.drive_link}" target="_blank" rel="noreferrer">open</a>` : 'Drive: not uploaded'}
            `;
            section.appendChild(item);
          });
          results.appendChild(section);
        });
      }

      function renderLiveJobs(payload) {
        results.style.display = 'block';
        results.innerHTML = '';
        payload.jobs.forEach((job) => {
          const section = document.createElement('div');
          section.className = 'job';
          section.innerHTML = `
            <p><strong>File:</strong> ${job.filename}</p>
            <p><strong>Status:</strong> ${job.status}</p>
            <p><strong>Stage:</strong> ${job.stage}</p>
            <p><strong>Progress:</strong> ${job.progress}%</p>
            ${job.error ? `<p><strong>Error:</strong> ${job.error}</p>` : ''}
          `;
          if (job.result) {
            const result = job.result;
            const resultBlock = document.createElement('div');
            resultBlock.innerHTML = `
              <p><strong>Transcript:</strong> ${result.transcript_path}</p>
              <p><strong>Manifest:</strong> ${result.manifest_path}</p>
            `;
            section.appendChild(resultBlock);
            (result.clips || []).forEach((clip) => {
              const item = document.createElement('div');
              item.className = 'clip';
              item.innerHTML = `
                <strong>${clip.title}</strong><br>
                Source: ${clip.source_start}s to ${clip.source_end}s<br>
                Captioned file: ${clip.captioned_path}<br>
                ${clip.drive_link ? `Drive: <a href="${clip.drive_link}" target="_blank" rel="noreferrer">open</a>` : 'Drive: not uploaded'}
              `;
              section.appendChild(item);
            });
          }
          results.appendChild(section);
        });
      }

      async function pollJobs() {
        if (!activeJobIds.length) return;
        const responses = await Promise.all(activeJobIds.map((jobId) => fetch(`/api/jobs/${jobId}`).then((r) => r.json())));
        renderLiveJobs({ jobs: responses });
        const completed = responses.filter((job) => job.status === 'completed' || job.status === 'failed');
        const avgProgress = Math.round(responses.reduce((sum, job) => sum + (job.progress || 0), 0) / responses.length);
        progressBar.style.width = `${avgProgress}%`;
        statusText.textContent = completed.length === responses.length ? 'Processing complete.' : 'Processing videos in CrewAI backend...';
        if (completed.length !== responses.length) {
          setTimeout(pollJobs, 1500);
        } else {
          submitButton.disabled = false;
        }
      }

      form.addEventListener('submit', (event) => {
        event.preventDefault();
        clearError();
        results.style.display = 'none';
        if (!input.files || !input.files.length) {
          showError('Choose at least one .mp4 or .mov file.');
          return;
        }

        const formData = new FormData(form);
        statusBox.style.display = 'block';
        statusText.textContent = 'Uploading videos...';
        progressBar.style.width = '0%';
        submitButton.disabled = true;

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/');

        xhr.upload.addEventListener('progress', (event) => {
          if (!event.lengthComputable) return;
          const percent = Math.round((event.loaded / event.total) * 100);
          progressBar.style.width = `${percent}%`;
          statusText.textContent = `Uploading... ${percent}%`;
        });

        xhr.onreadystatechange = () => {
          if (xhr.readyState !== XMLHttpRequest.DONE) return;
          submitButton.disabled = false;
          progressBar.style.width = '100%';
          statusText.textContent = 'Processing complete.';
          try {
            const payload = JSON.parse(xhr.responseText);
            if (xhr.status >= 400) {
              showError(payload.error || 'Upload failed.');
              submitButton.disabled = false;
              return;
            }
            activeJobIds = payload.job_ids || [];
            statusText.textContent = 'Upload complete. Starting jobs...';
            pollJobs();
          } catch (_error) {
            showError('The server returned an unexpected response.');
            submitButton.disabled = false;
          }
        };

        xhr.onerror = () => {
          submitButton.disabled = false;
          showError('Network error while uploading files.');
        };

        xhr.send(formData);
        setTimeout(() => {
          statusText.textContent = 'Upload finished. Processing videos, captions, and exports...';
        }, 1200);
      });
    </script>
  </body>
</html>
"""


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
    return render_template_string(HTML)


@app.get("/api/jobs/<job_id>")
def job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job.model_dump()), 200


if __name__ == "__main__":
    app.run(debug=True)
