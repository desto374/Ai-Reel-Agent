from __future__ import annotations

import argparse
import json
from pathlib import Path

from .crew import build_crew
from .helpers import ensure_dir, new_job_id
from .models import JobManifest
from .settings import Settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the CrewAI reels workflow.")
    parser.add_argument("--input-video", required=True, help="Absolute path or URL for the source video.")
    parser.add_argument("--output-count", type=int, default=4, help="How many reel candidates to generate.")
    parser.add_argument("--clip-length-min", type=int, default=30, help="Minimum clip length in seconds.")
    parser.add_argument("--clip-length-max", type=int, default=60, help="Maximum clip length in seconds.")
    parser.add_argument("--style-profile", default="podcast_reels", help="Short-form style profile.")
    parser.add_argument("--brand-logo", default="", help="Optional path to a logo asset.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings.from_env()

    job_id = new_job_id()
    workdir = ensure_dir(settings.reels_workdir / job_id)

    manifest = JobManifest(
        job_id=job_id,
        input_video=args.input_video,
        output_count=args.output_count,
        clip_length_min=args.clip_length_min,
        clip_length_max=args.clip_length_max,
        style_profile=args.style_profile,
        google_drive_folder_id=settings.google_drive_output_folder_id,
        working_dir=workdir,
        branding={
            "captions": True,
            "logo_path": args.brand_logo,
        },
    )

    crew = build_crew()
    result = crew.kickoff(inputs={"job_manifest": json.dumps(manifest.to_dict(), indent=2)})
    print(result)


if __name__ == "__main__":
    main()
