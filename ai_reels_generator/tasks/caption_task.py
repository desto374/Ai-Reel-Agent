from crewai import Task

from agents.caption_agent import build_caption_agent


def build_caption_task() -> Task:
    return Task(
        description=(
            "Generate readable subtitle files for each rendered clip and burn captions "
            "into the final vertical video outputs."
        ),
        expected_output="Captioned clip paths and SRT file paths.",
        agent=build_caption_agent(),
    )
