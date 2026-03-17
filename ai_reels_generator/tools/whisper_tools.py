from __future__ import annotations

import os
from pathlib import Path

from openai import OpenAI

from models.schemas import TranscriptBundle, TranscriptSegment


def transcribe_audio(audio_path: str) -> TranscriptBundle:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    audio_file = Path(audio_path)
    client = OpenAI(api_key=api_key)

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
