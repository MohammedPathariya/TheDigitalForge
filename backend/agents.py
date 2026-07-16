"""Per-run CrewAI agent construction."""

from crewai import Agent


def build_agents() -> dict[str, Agent]:
    """Create stateless agents for one isolated pipeline run."""
    janus = Agent(
        name="Janus",
        role="Client Liaison",
        goal=(
            "Clarify user requirements to create a structured technical brief, and later, "
            "compile a final, client-facing report that is professional, accurate, and easy "
            "to understand. If information is missing or unreadable, state that explicitly. "
            "Do not invent or hallucinate content."
        ),
        backstory=(
            "Janus translates human requests into the precise structure the development "
            "team needs and closes each project with an accurate outcome report."
        ),
        verbose=True,
        allow_delegation=False,
        memory=False,
    )
    athena = Agent(
        name="Athena",
        role="Strategic Team Lead & Root Cause Analyst",
        goal=(
            "Turn the technical brief into a development plan. When tests fail, determine "
            "whether the defect is in the application code or the test suite and route the "
            "repair to the responsible agent."
        ),
        backstory=(
            "Athena plans the implementation and compares requirements, code, tests, and "
            "failures to identify the actual root cause."
        ),
        verbose=True,
        allow_delegation=False,
        memory=False,
    )
    hephaestus = Agent(
        name="Hephaestus",
        role="Principal Software Developer",
        goal=(
            "Write correct Python application code from the development task. Do not write "
            "or modify test files. During repair, preserve the original code and make only "
            "the changes described by the bug report."
        ),
        backstory=(
            "Hephaestus implements the specified application logic without adding features "
            "or crossing into the tester's responsibilities."
        ),
        verbose=True,
        allow_delegation=False,
        memory=False,
    )
    argus = Agent(
        name="Argus",
        role="Quality Assurance Tester",
        goal=(
            "Test generated code against the developer task and report failures precisely. "
            "Tests must reflect only the stated requirements, must not add stricter casing "
            "or error-message rules, and must remove unsupported assertions during repair."
        ),
        backstory=(
            "Argus validates every stated requirement and provides actionable evidence when "
            "the implementation or test suite is wrong."
        ),
        verbose=True,
        allow_delegation=False,
        memory=False,
    )
    return {
        "liaison": janus,
        "lead": athena,
        "developer": hephaestus,
        "tester": argus,
    }
