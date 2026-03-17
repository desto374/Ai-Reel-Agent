from crewai import Agent


def build_clip_selector_agent() -> Agent:
    return Agent(
        role="Clip Selection Strategist",
        goal="Choose the most engaging short-form segments from a timestamped transcript.",
        backstory=(
            "An editor specialized in extracting high-retention moments for reels, "
            "shorts, and TikTok-style clips."
        ),
        llm="gpt-4o-mini",
        verbose=True,
        allow_delegation=False,
    )
