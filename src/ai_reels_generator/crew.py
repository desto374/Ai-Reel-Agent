from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2] / "ai_reels_generator"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def crew():
    from workflows.reels_pipeline import build_reels_pipeline

    return build_reels_pipeline()


def kickoff(inputs: dict | None = None):
    from workflows.reels_pipeline import build_reels_pipeline

    workflow = build_reels_pipeline()
    return workflow.kickoff(inputs=inputs or {})
