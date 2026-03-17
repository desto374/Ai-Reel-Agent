from __future__ import annotations

import os
import tempfile
from pathlib import Path

from openai import OpenAI

from models.schemas import TranscriptBundle, TranscriptSegment
from tools.ffmpeg_tools import estimate_chunk_count, prepare_transcription_audio, split_audio_chunks


MAX_TRANSCRIPTION_BYTES = 24 * 1024 * 1024
DEFAULT_CHUNK_SECONDS = 480


def transcribe_audio(audio_path: str) -> TranscriptBundle:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    audio_file = Path(audio_path)
    client = OpenAI(api_key=api_key)
    with tempfile.TemporaryDirectory(prefix="transcribe_audio_") as temp_dir:
        prepared_audio = Path(temp_dir) / f"{audio_file.stem}_transcription.mp3"
        prepare_transcription_audio(str(audio_file), str(prepared_audio))

        if prepared_audio.stat().st_size <= MAX_TRANSCRIPTION_BYTES:
            return _transcribe_single_file(client, prepared_audio)

        chunk_dir = Path(temp_dir) / "chunks"
        chunk_count = estimate_chunk_count(prepared_audio.stat().st_size, MAX_TRANSCRIPTION_BYTES)
        chunk_seconds = max(120, DEFAULT_CHUNK_SECONDS // max(1, chunk_count))
        chunk_paths = split_audio_chunks(str(prepared_audio), str(chunk_dir), chunk_seconds=chunk_seconds)

        merged_segments: list[TranscriptSegment] = []
        raw_text_parts: list[str] = []
        for index, chunk_path in enumerate(chunk_paths):
            chunk_bundle = _transcribe_single_file(client, Path(chunk_path))
            offset = index * chunk_seconds
            merged_segments.extend(
                TranscriptSegment(
                    start=segment.start + offset,
                    end=segment.end + offset,
                    text=segment.text,
                )
                for segment in chunk_bundle.segments
            )
            if chunk_bundle.raw_text:
                raw_text_parts.append(chunk_bundle.raw_text)

        return TranscriptBundle(
            segments=merged_segments,
            raw_text=" ".join(raw_text_parts).strip(),
        )


def _transcribe_single_file(client: OpenAI, audio_file: Path) -> TranscriptBundle:
    with audio_file.open("rb") as file_handle:
        transcription = client.audio.transcriptions.create(
            file=file_handle,
            model="whisper-1",
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )

    segments = [
        TranscriptSegment(
            start=float(segment.start),
            end=float(segment.end),
            text=segment.text.strip(),
        )
        for segment in getattr(transcription, "segments", []) or []
        if segment.text.strip()
    ]

    return TranscriptBundle(
        segments=segments,
        raw_text=getattr(transcription, "text", "").strip(),
    )
