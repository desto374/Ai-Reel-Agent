from crewai import Agent


def build_export_agent() -> Agent:
    return Agent(
        role="Export Coordinator",
        goal="Store final outputs, manifests, and delivery metadata for each rendered clip.",
        backstory=(
            "A delivery specialist responsible for organizing exported assets, "
            "preparing manifests, and handing off links or file paths."
        ),
        llm="gpt-4o-mini",
        verbose=True,
        allow_delegation=False,
    )
