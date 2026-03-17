from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ClipCandidate:
    clip_id: str
    title: str
    start_seconds: float
    end_seconds: float
    score: float
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class JobManifest:
    job_id: str
    input_video: str
    output_count: int
    clip_length_min: int
    clip_length_max: int
    style_profile: str
    google_drive_folder_id: str | None
    working_dir: Path
    branding: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["working_dir"] = str(self.working_dir)
        return payload
