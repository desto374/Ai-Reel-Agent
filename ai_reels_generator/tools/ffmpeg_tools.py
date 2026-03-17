from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path

HOSTED_VIDEO_WIDTH = 720
HOSTED_VIDEO_HEIGHT = 1280
HOSTED_VIDEO_CRF = "30"
HOSTED_PRESET = "veryfast"
HOSTED_AUDIO_BITRATE = "96k"


def run_cmd(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def ensure_ffmpeg() -> str:
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path

    try:
        from imageio_ffmpeg import get_ffmpeg_exe

        return get_ffmpeg_exe()
    except Exception as exc:
        raise RuntimeError("ffmpeg is not installed and no bundled ffmpeg binary is available.") from exc


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


def create_edit_proxy(video_path: str, output_path: str) -> str:
    ffmpeg = ensure_ffmpeg()
    run_cmd(
        [
            ffmpeg,
            "-y",
            "-i",
            video_path,
            "-vf",
            "scale='min(1280,iw)':-2",
            "-c:v",
            "libx264",
            "-preset",
            HOSTED_PRESET,
            "-crf",
            "31",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            HOSTED_AUDIO_BITRATE,
            output_path,
        ]
    )
    return output_path


def prepare_transcription_audio(input_audio_path: str, output_audio_path: str) -> str:
    ffmpeg = ensure_ffmpeg()
    run_cmd(
        [
            ffmpeg,
            "-y",
            "-i",
            input_audio_path,
            "-ac",
            "1",
            "-ar",
            "16000",
            "-b:a",
            "32k",
            output_audio_path,
        ]
    )
    return output_audio_path


def split_audio_chunks(input_audio_path: str, output_dir: str, chunk_seconds: int = 480) -> list[str]:
    ffmpeg = ensure_ffmpeg()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    pattern = output_path / "chunk_%03d.mp3"
    run_cmd(
        [
            ffmpeg,
            "-y",
            "-i",
            input_audio_path,
            "-f",
            "segment",
            "-segment_time",
            str(chunk_seconds),
            "-reset_timestamps",
            "1",
            "-c",
            "copy",
            str(pattern),
        ]
    )
    return [str(path) for path in sorted(output_path.glob("chunk_*.mp3"))]


def estimate_chunk_count(file_size_bytes: int, max_chunk_bytes: int) -> int:
    return max(1, math.ceil(file_size_bytes / max_chunk_bytes))


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
            "-preset",
            HOSTED_PRESET,
            "-crf",
            HOSTED_VIDEO_CRF,
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            HOSTED_AUDIO_BITRATE,
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
            f"scale={HOSTED_VIDEO_WIDTH}:{HOSTED_VIDEO_HEIGHT}:force_original_aspect_ratio=increase,crop={HOSTED_VIDEO_WIDTH}:{HOSTED_VIDEO_HEIGHT}",
            "-c:v",
            "libx264",
            "-preset",
            HOSTED_PRESET,
            "-crf",
            HOSTED_VIDEO_CRF,
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            HOSTED_AUDIO_BITRATE,
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
            "-preset",
            HOSTED_PRESET,
            "-crf",
            HOSTED_VIDEO_CRF,
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            HOSTED_AUDIO_BITRATE,
            output_path,
        ]
    )
    return output_path


def touch_placeholder(path: str) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.touch(exist_ok=True)
    return str(output)
