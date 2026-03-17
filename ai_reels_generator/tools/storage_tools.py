from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from tools.utils import ensure_dir, write_json


def save_manifest(output_path: str, payload: dict[str, Any]) -> str:
    path = Path(output_path)
    ensure_dir(path.parent)
    write_json(path, payload)
    return str(path)


def export_to_google_drive(
    file_path: str,
    service_account_file: str,
    folder_id: str | None = None,
) -> dict[str, str | None]:
    if not service_account_file:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_FILE is not set.")

    scopes = ["https://www.googleapis.com/auth/drive.file"]
    credentials = Credentials.from_service_account_file(service_account_file, scopes=scopes)
    drive_service = build("drive", "v3", credentials=credentials)

    file_name = Path(file_path).name
    mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
    metadata: dict[str, Any] = {"name": file_name}
    if folder_id:
        metadata["parents"] = [folder_id]

    media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
    created = (
        drive_service.files()
        .create(body=metadata, media_body=media, fields="id, webViewLink, webContentLink")
        .execute()
    )

    return {
        "status": "uploaded",
        "file_path": file_path,
        "folder_id": folder_id,
        "file_id": created.get("id"),
        "web_view_link": created.get("webViewLink"),
        "web_content_link": created.get("webContentLink"),
    }
