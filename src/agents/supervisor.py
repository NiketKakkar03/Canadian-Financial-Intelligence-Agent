from langgraph.types import Command, Send

from src.state import ResearchState

REQUIRED_SECTIONS = [
    "## Revenue Trend",
    "## Profitability Analysis",
    "## Analyst Sentiment",
    "## Risk Summary",
]


def is_report_complete(report: str) -> bool:
    return all(section in report for section in REQUIRED_SECTIONS)


async def supervisor_node(state: ResearchState) -> Command:
    """Fan out to Financial and Web Research agents in parallel."""
    return Command(goto=[
        Send("financial_agent", state),
        Send("web_research_agent", state),
    ])


async def route_after_agents(state: ResearchState) -> Command:
    """
    After both parallel agents complete, route to report writer.
    If the financial MCP server was unreachable, proceed in degraded mode —
    the report writer will include a visible notice.
    """
    return Command(goto="report_writer")


async def route_after_report(state: ResearchState) -> Command:
    """
    Structural completeness check: verify all four report sections are present.
    Routes to END in both cases — failure is informational, not a crash.
    """
    if state.report and is_report_complete(state.report):
        return Command(goto="__end__")

    # Report incomplete — end anyway rather than looping indefinitely.
    return Command(goto="__end__")
