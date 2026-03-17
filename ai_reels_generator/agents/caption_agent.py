from crewai import Agent


def build_caption_agent() -> Agent:
    return Agent(
        role="Caption Formatting Assistant",
        goal="Generate readable mobile-friendly subtitle files and captioned outputs.",
        backstory=(
            "A subtitle editor that keeps lines short, readable, and synchronized "
            "for mobile viewing."
        ),
        llm="gpt-4o-mini",
        verbose=True,
        allow_delegation=False,
    )
