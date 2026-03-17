from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    openai_api_key: str | None
    google_drive_output_folder_id: str | None
    google_service_account_file: str | None
    reels_workdir: Path

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            google_drive_output_folder_id=os.getenv("GOOGLE_DRIVE_OUTPUT_FOLDER_ID"),
            google_service_account_file=os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE"),
            reels_workdir=Path(os.getenv("REELS_WORKDIR", "./data/jobs")).resolve(),
        )
