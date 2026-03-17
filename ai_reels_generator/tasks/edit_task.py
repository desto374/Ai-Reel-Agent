from crewai import Task

from agents.video_editor_agent import build_video_editor_agent


def build_edit_task() -> Task:
    return Task(
        description=(
            "Cut the selected source clips and convert them into vertical 9:16 video "
            "outputs suitable for reels and shorts."
        ),
        expected_output="Rendered vertical clip file paths with source timing metadata.",
        agent=build_video_editor_agent(),
    )
