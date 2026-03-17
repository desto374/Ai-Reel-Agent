from crewai import Task

from agents.export_agent import build_export_agent


def build_export_task() -> Task:
    return Task(
        description=(
            "Persist final videos, transcripts, metadata, and export manifests. "
            "Prepare placeholder Drive upload metadata if cloud delivery is enabled."
        ),
        expected_output="Export manifest with clip paths, transcript paths, and delivery info.",
        agent=build_export_agent(),
    )
