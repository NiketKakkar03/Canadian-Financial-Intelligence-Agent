import os
from langchain_anthropic import ChatAnthropic
from src.state import ResearchState

_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

_UNAVAILABLE_NOTICE = (
    "> **Note:** Structured financial data was unavailable because the TSX Financial Data MCP server "
    "could not be reached. The sections below are based on web research only."
)


async def report_writer_agent(state: ResearchState) -> dict:
    financials_section = (
        _UNAVAILABLE_NOTICE if state.financial_agent_error or state.financials is None
        else state.financials
    )
    web_section = state.web_research or "_No web research available._"

    prompt = f"""You are a Canadian equity research analyst. Using the data below, write a structured Markdown investment brief with exactly these four sections:

## Revenue Trend
## Profitability Analysis
(Cover Net Income, Operating Income, and Gross Margin.)
## Analyst Sentiment
## Risk Summary

Financial data:
{financials_section}

Analyst commentary and news:
{web_section}

Write the brief now. Use only the data provided — do not invent figures."""

    llm = ChatAnthropic(model=_MODEL)
    response = await llm.ainvoke([{"role": "user", "content": prompt}])
    return {"report": response.content}
