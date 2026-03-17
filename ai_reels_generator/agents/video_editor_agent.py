from crewai import Agent


def build_video_editor_agent() -> Agent:
    return Agent(
        role="Video Editing Specialist",
        goal="Cut source clips and prepare vertical video outputs using deterministic editing tools.",
        backstory=(
            "A technical editor focused on clean clip extraction, mobile framing, "
            "and reliable production exports."
        ),
        llm="gpt-4o-mini",
        verbose=True,
        allow_delegation=False,
    )
