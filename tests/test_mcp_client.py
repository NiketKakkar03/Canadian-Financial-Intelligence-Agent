import pytest
from src.mcp_client import get_mcp_tools

pytestmark = pytest.mark.integration


async def test_get_mcp_tools():
    tools = await get_mcp_tools()
    names = [t.name for t in tools]

    assert isinstance(tools, list)
    assert len(tools) > 0

    # financial MCP server tools
    assert "summarize_quarter" in names
    assert "search_filings" in names

    # Tavily MCP server tools
    assert any("tavily" in n.lower() or "search" in n.lower() for n in names)
