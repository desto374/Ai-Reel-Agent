# CrewAI Workflow Design: Long-Form Video to Reels

## Goal

Build a CrewAI workflow that takes a long-form video, finds the strongest short-form moments, reformats them into vertical reel-style videos, and uploads the finished exports into Google Drive.

## Core User Flow

1. User uploads or submits a long-form video file or URL.
2. Workflow downloads and normalizes the source video.
3. AI transcribes the audio and analyzes the content.
4. AI selects the best moments for short-form clips.
5. Workflow cuts those moments into clips.
6. Auto-reframe centers the speaker or main subject for 9:16 output.
7. Captions and optional branding are added.
8. Quality checks run on each clip.
9. Final clips are uploaded to a Google Drive folder.
10. Workflow returns Drive links and a production summary.

## Recommended CrewAI Architecture

CrewAI should orchestrate decisions and task handoffs. Heavy media work should stay in tools and services, not inside the LLM.

### Agent 1: Intake Coordinator

Purpose:
- Validate the input video.
- Create a job ID and output folder structure.
- Decide whether the job is ready to process.

Inputs:
- Video URL or uploaded file path
- Desired clip length range
- Target style
- Google Drive destination folder ID

Outputs:
- Normalized job payload
- Processing manifest

### Agent 2: Transcription Analyst

Purpose:
- Extract audio
- Run speech-to-text
- Segment transcript by timestamps
- Identify topic shifts, strong hooks, emotional moments, and quotable sections

Recommended tools:
- `ffmpeg` for audio extraction
- OpenAI transcription model or Whisper-compatible endpoint

Outputs:
- Full transcript
- Time-aligned segments
- Content analysis notes

### Agent 3: Clip Strategist

Purpose:
- Score candidate moments for short-form performance
- Choose clips based on hook strength, clarity, emotional intensity, novelty, and standalone value

Selection rules:
- Default output: 3 to 5 clips
- Preferred duration: 30 to 60 seconds
- Avoid weak intros, dead air, filler, or context-heavy sections that do not stand alone
- Favor moments with a strong first 3 seconds

Outputs:
- Ranked clip candidates
- Start/end timestamps
- Reason for each selection
- Suggested title or hook line

### Agent 4: Video Editor Agent

Purpose:
- Cut source video into selected clips
- Clean audio if needed
- Normalize loudness

Recommended tools:
- `ffmpeg`
- Optional audio enhancement service

Outputs:
- Raw horizontal clip files

### Agent 5: Reframing Agent

Purpose:
- Convert clips to vertical 9:16
- Keep the speaker or main subject centered
- Handle scenes with multiple people or movement

Recommended tools:
- `ffmpeg`
- Subject detection/tracking model
- Optional services such as OpenCV, MediaPipe, YOLO, or a hosted video reframing API

Outputs:
- Vertical clips at `1080x1920`

Decision logic:
- If one face is dominant, center on that face
- If two faces matter, use dynamic crop or split layout
- If no face is visible, use safe center crop with scene saliency

### Agent 6: Caption and Packaging Agent

Purpose:
- Generate burned-in captions
- Apply branding presets if wanted
- Add title text, progress bars, or logo

Recommended tools:
- Subtitle generator from transcript timestamps
- `ffmpeg` subtitle burn-in

Outputs:
- Captioned vertical reel exports

### Agent 7: QA and Delivery Agent

Purpose:
- Verify each export meets quality rules
- Upload finished clips to Google Drive
- Return links and metadata

QA checks:
- Clip duration within target range
- Subject stays in frame
- Captions are synced and not cut off
- Audio is intelligible
- Export resolution is `1080x1920`
- File naming is consistent

Outputs:
- Final Google Drive URLs
- Job summary JSON
- Failure report if any clip needs reprocessing

## Suggested Workflow Sequence

```text
Input Video
  -> Intake Coordinator
  -> Transcription Analyst
  -> Clip Strategist
  -> Video Editor Agent
  -> Reframing Agent
  -> Caption and Packaging Agent
  -> QA and Delivery Agent
  -> Google Drive Folder + Result Summary
```

## Practical Enhancements You Should Add

These are worth adding even if your first version is simple:

### 1. Clip scoring rubric

Each candidate clip should be scored on:
- Hook strength
- Emotional intensity
- Clarity without extra context
- Speaker energy
- Shareability
- Relevance to target audience

This makes clip selection more consistent than just asking an LLM to "find exciting parts."

### 2. Retry path

If QA fails:
- Reframe again with a wider crop
- Regenerate captions with safer margins
- Shorten the clip if the pacing is weak

### 3. Style profiles

Let the user choose:
- Podcast reels
- Talking-head educational clips
- Motivational clips
- Interview clips

Each profile can change:
- Clip length
- Caption style
- Hook preference
- Framing rules

### 4. Metadata output

For each reel, save:
- Clip title
- Start/end timestamps
- Transcript snippet
- Score
- Export path
- Drive link

This will help if you later build a dashboard.

### 5. Human approval mode

Good for early versions:
- Auto-select clips
- Save preview files
- Let user approve before final export and upload

This reduces bad clips while you tune scoring.

## Tool Layer Recommendation

Use CrewAI agents for decisions. Use tools for execution.

### Good tool boundaries

- `download_video(url_or_path)`
- `extract_audio(video_path)`
- `transcribe_audio(audio_path)`
- `analyze_transcript(transcript_json)`
- `select_best_clips(transcript_json, analysis_json, style_profile)`
- `cut_clip(video_path, start_time, end_time)`
- `auto_reframe(clip_path, target_aspect="9:16")`
- `generate_captions(transcript_segment)`
- `burn_captions(video_path, srt_path)`
- `run_qa(video_path)`
- `upload_to_drive(file_path, folder_id)`

## Example Job Payload

```json
{
  "input_video": "https://youtube.com/watch?v=example",
  "output_count": 4,
  "clip_length_min": 30,
  "clip_length_max": 60,
  "style_profile": "podcast_reels",
  "branding": {
    "captions": true,
    "logo_path": "assets/logo.png"
  },
  "google_drive_folder_id": "drive_folder_123"
}
```

## Example Final Output

```json
{
  "job_id": "reels_job_001",
  "source_video": "input.mp4",
  "clips": [
    {
      "clip_id": "clip_01",
      "title": "Strong opening hook",
      "start": "00:02:14",
      "end": "00:02:58",
      "score": 9.2,
      "drive_url": "https://drive.google.com/..."
    }
  ]
}
```

## CrewAI Process Recommendation

Use a sequential process first.

Reason:
- Video pipelines are stateful
- Each step depends on structured outputs from the previous step
- Easier to debug than a fully autonomous agent swarm

Later, you can parallelize only the clip post-processing stage:
- Multiple selected clips can be cut, reframed, captioned, and QA-checked in parallel

## Recommended Stack

- CrewAI for orchestration
- Python for tools and pipeline code
- `ffmpeg` for video editing
- OpenAI transcription + language model analysis
- OpenCV or MediaPipe for face/subject tracking
- Google Drive API for delivery
- Optional queue layer such as Redis/Celery if jobs get large

## MVP Version

If you want the fastest version that works:

1. Input video
2. Extract audio
3. Transcribe
4. LLM selects top 3 to 5 clips
5. Cut clips with `ffmpeg`
6. Convert to vertical center crop
7. Add captions
8. Upload to Google Drive

This is the simplest path, but center crop alone will fail on some videos. The first major upgrade after MVP should be smart subject tracking for reframing.

## Better Production Version

1. Ingest and normalize video
2. Transcribe with timestamps
3. Score candidate moments with a clip rubric
4. Cut selected clips
5. Run subject-aware auto-reframe
6. Add dynamic captions
7. Run automated QA
8. Retry failed clips
9. Upload approved clips to Google Drive
10. Save structured metadata for each job

## What I Recommend You Build First

Start with this exact scope:

1. One CrewAI crew
2. Five agents:
   - Intake Coordinator
   - Transcription Analyst
   - Clip Strategist
   - Reframing Agent
   - QA and Delivery Agent
3. Tools backed by `ffmpeg`, transcription, and Drive upload
4. One style profile
5. Human approval toggle

That is enough to prove the workflow without overbuilding.

## Implementation Note

The LLM should not directly manipulate video files. It should only:
- analyze transcript and clip potential
- choose timestamps
- decide retries
- produce metadata and instructions for tools

All media processing should happen in deterministic Python tools.
