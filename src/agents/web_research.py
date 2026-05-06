import os
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

from src.mcp_client import get_mcp_tools
from src.state import ResearchState

_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")


async def web_research_agent(state: ResearchState) -> dict:
    try:
        tools = await get_mcp_tools()
        tavily_tools = [t for t in tools if t.name not in ("summarize_quarter", "search_filings")]

        llm = ChatAnthropic(model=_MODEL)
        agent = create_react_agent(llm, tavily_tools)

        prompt = (
            f"Research query: {state.query}\n\n"
            "Search for recent analyst commentary, earnings reactions, and news about this company. "
            "Focus on analyst sentiment, price target changes, and any material recent developments."
        )

        result = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
        web_research = result["messages"][-1].content
        return {"web_research": web_research, "web_research_agent_error": False}

    except Exception:
        return {"web_research": None, "web_research_agent_error": True}
