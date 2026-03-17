from crewai import Task

from agents.transcription_agent import build_transcription_agent


def build_transcription_task() -> Task:
    return Task(
        description=(
            "Extract audio from the source video, produce a timestamped transcript, "
            "and save transcript artifacts for downstream clip analysis."
        ),
        expected_output="Transcript bundle JSON with timestamped segments and raw text.",
        agent=build_transcription_agent(),
    )
