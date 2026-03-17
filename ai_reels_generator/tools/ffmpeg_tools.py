from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def run_cmd(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def ensure_ffmpeg() -> str:
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        raise RuntimeError("ffmpeg is not installed or not available on PATH.")
    return ffmpeg_path


def extract_audio(video_path: str, audio_path: str) -> str:
    ffmpeg = ensure_ffmpeg()
    run_cmd(
        [
            ffmpeg,
            "-y",
            "-i",
            video_path,
            "-vn",
            "-acodec",
            "pcm_s16le",
            audio_path,
        ]
    )
    return audio_path


def cut_clip(video_path: str, start: float, end: float, output_path: str) -> str:
    ffmpeg = ensure_ffmpeg()
    run_cmd(
        [
            ffmpeg,
            "-y",
            "-i",
            video_path,
            "-ss",
            str(start),
            "-to",
            str(end),
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            output_path,
        ]
    )
    return output_path


def to_vertical(input_path: str, output_path: str) -> str:
    ffmpeg = ensure_ffmpeg()
    run_cmd(
        [
            ffmpeg,
            "-y",
            "-i",
            input_path,
            "-vf",
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            output_path,
        ]
    )
    return output_path


def burn_subtitles(video_path: str, srt_path: str, output_path: str) -> str:
    ffmpeg = ensure_ffmpeg()
    run_cmd(
        [
            ffmpeg,
            "-y",
            "-i",
            video_path,
            "-vf",
            f"subtitles={srt_path}",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            output_path,
        ]
    )
    return output_path


def touch_placeholder(path: str) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.touch(exist_ok=True)
    return str(output)
