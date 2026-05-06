from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ResearchState:
    query: str = ""
    thread_id: str = ""
    financials: Optional[str] = None
    web_research: Optional[str] = None
    report: Optional[str] = None
    financial_agent_error: bool = False
    web_research_agent_error: bool = False
