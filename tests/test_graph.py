import uuid
import pytest

from src.agents.supervisor import REQUIRED_SECTIONS
from src.graph import build_graph
from src.state import ResearchState

_COMPLETE_REPORT = "\n".join(f"{s}\ncontent" for s in REQUIRED_SECTIONS)

_FINANCIAL_OK = {"financials": "Revenue: $10B", "financial_agent_error": False}
_FINANCIAL_DOWN = {"financials": None, "financial_agent_error": True}
_WEB_OK = {"web_research": "Analysts bullish", "web_research_agent_error": False}
_REPORT_OK = {"report": _COMPLETE_REPORT}


def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def _input(thread_id: str | None = None) -> dict:
    return {"query": "RBC Q4 2024", "thread_id": thread_id or str(uuid.uuid4())}


def _make_node(return_value: dict):
    """Wrap a fixed return value in a proper async function LangGraph can inspect."""
    async def _node(state: ResearchState) -> dict:
        return return_value
    return _node


def _graph(financial=None, web=None, report=None):
    return build_graph(nodes={
        "financial_agent": _make_node(financial or _FINANCIAL_OK),
        "web_research_agent": _make_node(web or _WEB_OK),
        "report_writer": _make_node(report or _REPORT_OK),
    })


@pytest.mark.asyncio
async def test_graph_happy_path():
    graph = _graph()
    inp = _input()
    result = await graph.ainvoke(inp, config=_config(inp["thread_id"]))

    assert result["report"] == _COMPLETE_REPORT
    assert result["financial_agent_error"] is False
    assert result["web_research_agent_error"] is False


@pytest.mark.asyncio
async def test_graph_financial_mcp_down():
    graph = _graph(financial=_FINANCIAL_DOWN)
    inp = _input()
    result = await graph.ainvoke(inp, config=_config(inp["thread_id"]))

    assert result["financial_agent_error"] is True
    assert result["report"] is not None


@pytest.mark.asyncio
async def test_graph_checkpoint_thread_isolation():
    """
    Two runs with different thread_ids must produce independent results.
    Checkpointing stores state per thread_id — one thread's data must not
    bleed into another.
    """
    report_a = {"report": "## Revenue Trend\nA\n## Profitability Analysis\nA\n## Analyst Sentiment\nA\n## Risk Summary\nA"}
    report_b = {"report": "## Revenue Trend\nB\n## Profitability Analysis\nB\n## Analyst Sentiment\nB\n## Risk Summary\nB"}

    graph_a = _graph(report=report_a)
    graph_b = _graph(report=report_b)

    tid_a, tid_b = str(uuid.uuid4()), str(uuid.uuid4())

    result_a = await graph_a.ainvoke(_input(thread_id=tid_a), config=_config(tid_a))
    result_b = await graph_b.ainvoke(_input(thread_id=tid_b), config=_config(tid_b))

    assert "A" in result_a["report"]
    assert "B" in result_b["report"]
    assert result_a["report"] != result_b["report"]
