from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str


class ClipCandidate(BaseModel):
    title: str
    start: float
    end: float
    score: float = Field(ge=0.0, le=10.0)
    reason: str


class ClipCandidateList(BaseModel):
    clips: List[ClipCandidate]


class TranscriptBundle(BaseModel):
    segments: List[TranscriptSegment]
    raw_text: str


class RenderedClip(BaseModel):
    title: str
    source_start: float
    source_end: float
    clip_path: str
    vertical_path: Optional[str] = None
    captioned_path: Optional[str] = None
    srt_path: Optional[str] = None
    drive_file_id: Optional[str] = None
    drive_link: Optional[str] = None


class PipelineRunResult(BaseModel):
    source_video: str
    transcript_path: str
    manifest_path: str
    clips: List[RenderedClip]
