# CrewAI Reels Agent

This project is a starter CrewAI workflow for converting long-form videos into short-form vertical reels.

## What it does

1. Accepts a local video path or URL
2. Builds a processing manifest
3. Transcribes the source audio
4. Selects the strongest clip candidates
5. Cuts clips with `ffmpeg`
6. Creates a reframing plan for 9:16 output
7. Generates captions
8. Runs QA checks
9. Uploads final assets to Google Drive

## Current state

This is an MVP scaffold. It is designed to be runnable after you install dependencies and connect the external tools it expects:

- `crewai`
- `ffmpeg`
- OpenAI API key
- Google Drive service account credentials

The LLM agents handle orchestration and decision-making. Python tools handle deterministic work like audio extraction, clipping, file output, and uploads.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Then fill in `.env`.

## Run

```bash
python3 -m reels_agent.main \
  --input-video /absolute/path/to/video.mp4 \
  --output-count 4 \
  --clip-length-min 30 \
  --clip-length-max 60 \
  --style-profile podcast_reels
```

## Suggested next upgrades

- Add true subject tracking using OpenCV or MediaPipe
- Replace placeholder caption generation with word-level timestamps
- Add a preview approval step before upload
- Persist jobs to a database for retries and audit history
