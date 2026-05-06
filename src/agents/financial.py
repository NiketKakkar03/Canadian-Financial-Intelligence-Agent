import os
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

from src.mcp_client import get_mcp_tools
from src.state import ResearchState

_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")


async def financial_agent(state: ResearchState) -> dict:
    try:
        tools = await get_mcp_tools()
        financial_tools = [t for t in tools if t.name in ("summarize_quarter", "search_filings")]

        llm = ChatAnthropic(model=_MODEL)
        agent = create_react_agent(llm, financial_tools)

        prompt = (
            f"Research query: {state.query}\n\n"
            "1. Call summarize_quarter for the relevant TSX ticker (use trailing twelve months).\n"
            "2. Call search_filings for supplementary filing context on the same company.\n"
            "Return a structured summary covering revenue, profitability, and any key filing details."
        )

        result = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
        financials = result["messages"][-1].content
        return {"financials": financials, "financial_agent_error": False}

    except Exception:
        return {"financials": None, "financial_agent_error": True}
