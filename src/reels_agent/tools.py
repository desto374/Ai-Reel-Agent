from __future__ import annotations

import json
import os
import shutil
import wave
from pathlib import Path

from crewai.tools import BaseTool

from .helpers import ensure_dir, run_command, write_json
from .models import ClipCandidate, JobManifest


class PrepareJobTool(BaseTool):
    name: str = "prepare_job"
    description: str = "Validate input fields and create the working directory structure for a reel job."

    def _run(self, manifest_json: str) -> str:
        payload = json.loads(manifest_json)
        working_dir = ensure_dir(Path(payload["working_dir"]))
        ensure_dir(working_dir / "source")
        ensure_dir(working_dir / "audio")
        ensure_dir(working_dir / "transcripts")
        ensure_dir(working_dir / "clips")
        ensure_dir(working_dir / "exports")
        write_json(working_dir / "manifest.json", payload)
        return json.dumps(payload, indent=2)


class ExtractAudioTool(BaseTool):
    name: str = "extract_audio"
    description: str = "Extract mono WAV audio from the input video using ffmpeg."

    def _run(self, input_video: str, output_audio: str) -> str:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("ffmpeg is not installed or not available on PATH.")
        run_command(
            [
                ffmpeg,
                "-y",
                "-i",
                input_video,
                "-ac",
                "1",
                "-ar",
                "16000",
                output_audio,
            ]
        )
        return output_audio


class TranscribeAudioTool(BaseTool):
    name: str = "transcribe_audio"
    description: str = "Create a placeholder timestamped transcript for the extracted audio."

    def _run(self, audio_path: str, transcript_path: str) -> str:
        audio_file = Path(audio_path)
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        with wave.open(str(audio_file), "rb") as wav_file:
            frame_rate = wav_file.getframerate()
            frame_count = wav_file.getnframes()
            duration = frame_count / float(frame_rate)

        transcript = {
            "source_audio": audio_path,
            "duration_seconds": duration,
            "segments": [
                {
                    "start": 0,
                    "end": min(duration, 60),
                    "text": "Placeholder transcript segment. Replace this with a real transcription API call.",
                }
            ],
        }
        write_json(Path(transcript_path), transcript)
        return json.dumps(transcript, indent=2)


class SelectClipsTool(BaseTool):
    name: str = "select_clips"
    description: str = "Select clip candidates from a timestamped transcript using a simple heuristic fallback."

    def _run(
        self,
        transcript_json: str,
        output_count: int = 3,
        clip_length_min: int = 30,
        clip_length_max: int = 60,
    ) -> str:
        transcript = json.loads(transcript_json)
        segments = transcript.get("segments", [])
        candidates: list[ClipCandidate] = []

        for index, segment in enumerate(segments[:output_count], start=1):
            start = float(segment["start"])
            end = float(segment["end"])
            duration = end - start
            if duration < clip_length_min:
                end = start + clip_length_min
            if duration > clip_length_max:
                end = start + clip_length_max
            candidates.append(
                ClipCandidate(
                    clip_id=f"clip_{index:02d}",
                    title=f"Candidate clip {index}",
                    start_seconds=start,
                    end_seconds=end,
                    score=max(7.0, 9.5 - index * 0.3),
                    rationale="Fallback heuristic candidate based on transcript segment boundaries.",
                )
            )

        return json.dumps([candidate.to_dict() for candidate in candidates], indent=2)


class CutClipTool(BaseTool):
    name: str = "cut_clip"
    description: str = "Cut a clip from the source video using ffmpeg."

    def _run(self, input_video: str, start_seconds: float, end_seconds: float, output_clip: str) -> str:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("ffmpeg is not installed or not available on PATH.")
        run_command(
            [
                ffmpeg,
                "-y",
                "-ss",
                str(start_seconds),
                "-to",
                str(end_seconds),
                "-i",
                input_video,
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                output_clip,
            ]
        )
        return output_clip


class ReframeClipTool(BaseTool):
    name: str = "reframe_clip"
    description: str = "Convert a clip to a simple 9:16 vertical export using center crop as the MVP fallback."

    def _run(self, input_clip: str, output_clip: str) -> str:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("ffmpeg is not installed or not available on PATH.")
        run_command(
            [
                ffmpeg,
                "-y",
                "-i",
                input_clip,
                "-vf",
                "crop='min(iw,ih*9/16)':'ih',scale=1080:1920",
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                output_clip,
            ]
        )
        return output_clip


class GenerateCaptionsTool(BaseTool):
    name: str = "generate_captions"
    description: str = "Generate a basic SRT file from transcript segments."

    def _run(self, transcript_json: str, output_srt: str) -> str:
        transcript = json.loads(transcript_json)
        segments = transcript.get("segments", [])
        lines: list[str] = []
        for index, segment in enumerate(segments, start=1):
            lines.extend(
                [
                    str(index),
                    f"{_to_srt_time(segment['start'])} --> {_to_srt_time(segment['end'])}",
                    segment["text"],
                    "",
                ]
            )
        Path(output_srt).write_text("\n".join(lines), encoding="utf-8")
        return output_srt


class BurnCaptionsTool(BaseTool):
    name: str = "burn_captions"
    description: str = "Burn caption subtitles into a video export using ffmpeg."

    def _run(self, input_clip: str, srt_path: str, output_clip: str) -> str:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("ffmpeg is not installed or not available on PATH.")
        run_command(
            [
                ffmpeg,
                "-y",
                "-i",
                input_clip,
                "-vf",
                f"subtitles={srt_path}",
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                output_clip,
            ]
        )
        return output_clip


class RunQATool(BaseTool):
    name: str = "run_qa"
    description: str = "Verify that the expected output clip file exists and is non-empty."

    def _run(self, video_path: str) -> str:
        clip_path = Path(video_path)
        passed = clip_path.exists() and clip_path.stat().st_size > 0
        result = {
            "video_path": video_path,
            "passed": passed,
            "checks": [
                "file_exists",
                "non_empty_file",
            ],
        }
        return json.dumps(result, indent=2)


class UploadToDriveTool(BaseTool):
    name: str = "upload_to_drive"
    description: str = "Return a local-delivery placeholder until Google Drive upload is configured."

    def _run(self, file_path: str, folder_id: str = "") -> str:
        if not folder_id:
            folder_id = os.getenv("GOOGLE_DRIVE_OUTPUT_FOLDER_ID", "")
        result = {
            "file_path": file_path,
            "folder_id": folder_id,
            "status": "pending_google_drive_integration",
            "message": "Wire this tool to Google Drive API using a service account for production delivery.",
        }
        return json.dumps(result, indent=2)


def _to_srt_time(seconds: float) -> str:
    total_ms = int(seconds * 1000)
    hours = total_ms // 3_600_000
    minutes = (total_ms % 3_600_000) // 60_000
    secs = (total_ms % 60_000) // 1000
    millis = total_ms % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
