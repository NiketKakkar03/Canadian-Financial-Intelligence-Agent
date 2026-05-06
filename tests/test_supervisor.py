import pytest
from langgraph.types import Command, Send

from src.agents.supervisor import (
    REQUIRED_SECTIONS,
    is_report_complete,
    route_after_agents,
    route_after_report,
    supervisor_node,
)
from src.state import ResearchState

_COMPLETE_REPORT = "\n".join(f"{s}\ncontent" for s in REQUIRED_SECTIONS)
_INCOMPLETE_REPORT = "## Revenue Trend\ncontent"


# --- is_report_complete ---

def test_complete_report_passes():
    assert is_report_complete(_COMPLETE_REPORT) is True


def test_incomplete_report_fails():
    assert is_report_complete(_INCOMPLETE_REPORT) is False


def test_empty_report_fails():
    assert is_report_complete("") is False


# --- supervisor_node: fan-out ---

@pytest.mark.asyncio
async def test_supervisor_fans_out_to_both_agents():
    state = ResearchState(query="RBC Q4 2024")
    cmd = await supervisor_node(state)
    assert isinstance(cmd, Command)
    destinations = [s.node for s in cmd.goto]
    assert "financial_agent" in destinations
    assert "web_research_agent" in destinations


# --- route_after_agents: happy path and degraded ---

@pytest.mark.asyncio
async def test_route_after_agents_happy_path():
    state = ResearchState(financials="data", web_research="commentary")
    cmd = await route_after_agents(state)
    assert isinstance(cmd, Command)
    assert cmd.goto == "report_writer"


@pytest.mark.asyncio
async def test_route_after_agents_financial_mcp_down():
    """Degraded state: financial error flag set — still routes to report_writer."""
    state = ResearchState(financial_agent_error=True, web_research="commentary")
    cmd = await route_after_agents(state)
    assert isinstance(cmd, Command)
    assert cmd.goto == "report_writer"


# --- route_after_report: completeness check ---

@pytest.mark.asyncio
async def test_route_after_report_complete():
    state = ResearchState(report=_COMPLETE_REPORT)
    cmd = await route_after_report(state)
    assert isinstance(cmd, Command)
    assert cmd.goto == "__end__"


@pytest.mark.asyncio
async def test_route_after_report_incomplete():
    state = ResearchState(report=_INCOMPLETE_REPORT)
    cmd = await route_after_report(state)
    assert isinstance(cmd, Command)
    assert cmd.goto == "__end__"
