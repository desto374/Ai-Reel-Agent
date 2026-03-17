from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from config.settings import get_settings
from services.pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the AI reels pipeline.")
    parser.add_argument(
        "--video-path",
        default="input_videos/source.mp4",
        help="Path to the local MP4 or MOV source video.",
    )
    parser.add_argument("--output-count", type=int, default=5, help="How many reel candidates to render.")
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()
    settings = get_settings()

    video_path = Path(args.video_path)
    settings.ensure_directories()
    result = run_pipeline(
        video_path=video_path,
        settings=settings,
        output_count=args.output_count,
    )
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
