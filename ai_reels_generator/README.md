# AI Reels Generator

CrewAI starter project for turning one long-form video into multiple short vertical clips with captions, metadata, and export delivery.

## Features

- Modular Python package structure
- CrewAI orchestration
- Local upload screen for `.mp4` and `.mov`
- FFmpeg helper tools for extraction, cutting, vertical conversion, and subtitle burn-in
- Transcript, clip metadata, and export manifests
- OpenAI transcription with timestamps
- Google Drive upload via service account
- Typed schemas with Pydantic
- Starter tests for schemas and FFmpeg command construction

## Project layout

```text
ai_reels_generator/
  agents/
  tasks/
  tools/
  workflows/
  models/
  config/
  input_videos/
  outputs/
  tests/
  main.py
```

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Install `ffmpeg` separately for local development when possible. In hosted environments, the app can also fall back to the bundled `imageio-ffmpeg` binary.

CrewAI note:

- Use Python `3.11+`
- This project bootstraps CrewAI runtime storage into a local `.crewai_home/` folder so it can run cleanly from the project directory

Recommended local file layout:

- Keep your Google service account JSON under `credentials/`
- Upload source videos through the web UI or place manual test files under `input_videos/`
- Generated exports stay under `outputs/`

## Run

CLI:

```bash
python3 main.py --video-path input_videos/source.mp4 --output-count 5
```

Web upload screen:

```bash
export FLASK_APP=app
flask --app app run
```

Then open `http://127.0.0.1:5000`.

Production-style local run:

```bash
gunicorn app:app --workers 1 --threads 2 --timeout 300
```

## Inputs

- Local file path via CLI
- Browser upload via the landing screen
- Supported video formats: `.mp4`, `.mov`

## Environment

- `OPENAI_API_KEY`
- `GOOGLE_DRIVE_FOLDER_ID`
- `GOOGLE_SERVICE_ACCOUNT_FILE`
- `INPUT_VIDEO_PATH`
- `OUTPUT_DIR`

## Render Deployment

Recommended setup:

1. Deploy the repo with Render using the repository root.
2. Set the Render root directory to `ai_reels_generator` if you are not using the included root-level `render.yaml`.
3. Add environment variables in Render:
   - `OPENAI_API_KEY`
   - `GOOGLE_DRIVE_FOLDER_ID`
   - `GOOGLE_SERVICE_ACCOUNT_FILE`
   - `INPUT_VIDEO_PATH`
   - `OUTPUT_DIR`
4. Upload the Google service account JSON to Render as a secret file or mount it through your deploy flow.

Notes:

- The Flask app is the public trigger UI.
- CrewAI runs behind the Flask app.
- This app can use the bundled `imageio-ffmpeg` binary on Render, so `apt-get` is not required.
- For lower-memory hosting, use a single Gunicorn worker.
- For larger uploads or longer jobs, move processing to a background worker later.

## Recommended next steps

1. Add face tracking or subject detection before vertical cropping.
2. Improve caption styling for viral-style highlighted words.
3. Add a review step before final export or upload.
4. Route the runtime pipeline through CrewAI tasks instead of the current direct service layer.
