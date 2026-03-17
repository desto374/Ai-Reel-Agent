from crewai import Task

from agents.clip_selector_agent import build_clip_selector_agent
from models.schemas import ClipCandidateList


def build_clip_selection_task() -> Task:
    return Task(
        description=(
            "Given a timestamped transcript, return 5 clip candidates suitable for "
            "short-form platforms. Each clip should usually be 20 to 60 seconds."
        ),
        expected_output="Strict JSON list with title, start, end, score, and reason.",
        output_pydantic=ClipCandidateList,
        agent=build_clip_selector_agent(),
    )
