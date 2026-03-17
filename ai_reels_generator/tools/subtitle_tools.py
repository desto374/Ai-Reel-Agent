from __future__ import annotations

from pathlib import Path

from models.schemas import TranscriptBundle, TranscriptSegment


def to_srt_timestamp(seconds: float) -> str:
    total_milliseconds = int(seconds * 1000)
    hours = total_milliseconds // 3_600_000
    minutes = (total_milliseconds % 3_600_000) // 60_000
    secs = (total_milliseconds % 60_000) // 1000
    milliseconds = total_milliseconds % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def segment_to_srt(index: int, segment: TranscriptSegment) -> str:
    return (
        f"{index}\n"
        f"{to_srt_timestamp(segment.start)} --> {to_srt_timestamp(segment.end)}\n"
        f"{segment.text}\n"
    )


def write_srt(bundle: TranscriptBundle, output_path: str) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(segment_to_srt(index, segment) for index, segment in enumerate(bundle.segments, start=1))
    path.write_text(content + "\n", encoding="utf-8")
    return str(path)
