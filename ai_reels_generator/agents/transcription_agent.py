from crewai import Agent


def build_transcription_agent() -> Agent:
    return Agent(
        role="Transcription Specialist",
        goal="Generate accurate timestamped transcripts from source video audio.",
        backstory=(
            "An audio transcription specialist that prepares structured transcript data "
            "for clip analysis and downstream editing."
        ),
        llm="gpt-4o-mini",
        verbose=True,
        allow_delegation=False,
    )
