from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    openai_api_key: str
    google_drive_folder_id: str
    google_service_account_file: str
    google_service_account_json: str
    debug_webhook_url: str
    job_stall_seconds: int
    input_video_path: Path
    output_dir: Path
    uploads_dir: Path
    clips_dir: Path
    vertical_dir: Path
    captions_dir: Path
    transcripts_dir: Path
    manifests_dir: Path
    logs_dir: Path

    def ensure_directories(self) -> None:
        for path in [
            self.output_dir,
            self.uploads_dir,
            self.clips_dir,
            self.vertical_dir,
            self.captions_dir,
            self.transcripts_dir,
            self.manifests_dir,
            self.logs_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def resolved_google_service_account_file(self) -> str:
        if self.google_service_account_json:
            secrets_dir = self.output_dir / ".runtime_secrets"
            secrets_dir.mkdir(parents=True, exist_ok=True)
            secret_path = secrets_dir / "google-service-account.json"
            payload = json.loads(self.google_service_account_json)
            secret_path.write_text(json.dumps(payload), encoding="utf-8")
            return str(secret_path)

        if not self.google_service_account_file:
            return ""

        candidate = Path(self.google_service_account_file)
        if candidate.is_absolute():
            return str(candidate)

        return str(Path.cwd() / candidate)


def get_settings() -> Settings:
    output_dir = Path(os.getenv("OUTPUT_DIR", "outputs"))
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        google_drive_folder_id=os.getenv("GOOGLE_DRIVE_FOLDER_ID", ""),
        google_service_account_file=os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", ""),
        google_service_account_json=os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", ""),
        debug_webhook_url=os.getenv(
            "N8N_DEBUG_WEBHOOK_URL",
            os.getenv(
            "N8N_WEBHOOK_URL",
                os.getenv("DEBUG_WEBHOOK_URL", "https://desto374.app.n8n.cloud/webhook/auto-debug"),
            ),
        ),
        job_stall_seconds=int(os.getenv("JOB_STALL_SECONDS", "150")),
        input_video_path=Path(os.getenv("INPUT_VIDEO_PATH", "input_videos/source.mp4")),
        output_dir=output_dir,
        uploads_dir=Path("input_videos/uploads"),
        clips_dir=output_dir / "clips",
        vertical_dir=output_dir / "vertical",
        captions_dir=output_dir / "captions",
        transcripts_dir=output_dir / "transcripts",
        manifests_dir=output_dir / "manifests",
        logs_dir=output_dir / "logs",
    )
