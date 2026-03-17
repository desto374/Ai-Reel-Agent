from __future__ import annotations

import os
from pathlib import Path


def bootstrap_crewai_environment() -> None:
    project_root = Path(__file__).resolve().parent
    crewai_home = project_root / ".crewai_home"
    crewai_home.mkdir(parents=True, exist_ok=True)
    os.environ["HOME"] = str(crewai_home)
    os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
