import os
from langchain_mcp_adapters.client import MultiServerMCPClient

FINANCIAL_MCP_URL = os.getenv("FINANCIAL_MCP_URL", "http://localhost:8000/mcp")
TAVILY_MCP_URL = os.getenv("TAVILY_MCP_URL", "http://localhost:8001/mcp")


async def get_mcp_tools() -> list:
    client = MultiServerMCPClient(
        {
            "financial": {"url": FINANCIAL_MCP_URL, "transport": "streamable_http"}, # noqa: uses streamable-http per FastMCP default
            "tavily": {"url": TAVILY_MCP_URL, "transport": "sse"},
        }
    )
    return await client.get_tools()
