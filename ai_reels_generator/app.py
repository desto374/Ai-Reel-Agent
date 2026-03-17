from __future__ import annotations

from flask import Flask, redirect, render_template_string, request, url_for
from dotenv import load_dotenv

from config.settings import get_settings
from services.pipeline import run_pipeline, save_uploaded_video


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
      code { background: #f5eadb; padding: 2px 6px; border-radius: 6px; }
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="card">
        <h1>AI Reels Generator</h1>
        <p>Upload a long-form <code>.mp4</code> or <code>.mov</code> video. The pipeline will transcribe it, pick strong moments, render vertical clips, burn captions, and optionally upload the exports to Google Drive.</p>
        {% if error %}
          <div class="error">{{ error }}</div>
        {% endif %}
        <form method="post" enctype="multipart/form-data">
          <div>
            <label for="video">Video file</label><br>
            <input id="video" type="file" name="video" accept=".mp4,.mov" required>
          </div>
          <div>
            <label for="output_count">How many clips</label><br>
            <input id="output_count" type="number" name="output_count" min="1" max="10" value="5">
          </div>
          <button type="submit">Generate Reels</button>
        </form>
        {% if result %}
          <div class="result">
            <p><strong>Transcript:</strong> {{ result.transcript_path }}</p>
            <p><strong>Manifest:</strong> {{ result.manifest_path }}</p>
            {% for clip in result.clips %}
              <div class="clip">
                <strong>{{ clip.title }}</strong><br>
                Source: {{ clip.source_start }}s to {{ clip.source_end }}s<br>
                Captioned file: {{ clip.captioned_path }}<br>
                {% if clip.drive_link %}
                  Drive: <a href="{{ clip.drive_link }}" target="_blank" rel="noreferrer">open</a>
                {% else %}
                  Drive: not uploaded
                {% endif %}
              </div>
            {% endfor %}
          </div>
        {% endif %}
      </div>
    </div>
  </body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    settings = get_settings()
    settings.ensure_directories()
    if request.method == "POST":
        upload = request.files.get("video")
        if not upload or not upload.filename:
            return render_template_string(HTML, error="Choose an .mp4 or .mov file.", result=None)
        try:
            saved_video = save_uploaded_video(upload, settings.uploads_dir)
            result = run_pipeline(
                video_path=saved_video,
                settings=settings,
                output_count=int(request.form.get("output_count", "5")),
            )
            return render_template_string(HTML, result=result.model_dump(), error=None)
        except Exception as exc:
            return render_template_string(HTML, error=str(exc), result=None)
    return render_template_string(HTML, error=None, result=None)


if __name__ == "__main__":
    app.run(debug=True)
