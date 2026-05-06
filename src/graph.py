from contextlib import asynccontextmanager

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import START, StateGraph

from src.agents.financial import financial_agent
from src.agents.report_writer import report_writer_agent
from src.agents.supervisor import route_after_agents, route_after_report, supervisor_node
from src.agents.web_research import web_research_agent
from src.state import ResearchState


def build_graph(checkpointer=None, nodes: dict | None = None):
    """
    Wire all nodes, edges, and the checkpointer into a compiled LangGraph graph.

    checkpointer: pass a SqliteSaver (or any BaseCheckpointSaver) for persistence,
                  or leave None to use an in-memory checkpointer (tests).
    nodes: optional dict of node name → callable overrides, used in tests to inject
           mocked agent functions without patching module-level references.
    """
    if checkpointer is None:
        checkpointer = MemorySaver()

    overrides = nodes or {}

    builder = StateGraph(ResearchState)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("financial_agent", overrides.get("financial_agent", financial_agent))
    builder.add_node("web_research_agent", overrides.get("web_research_agent", web_research_agent))
    builder.add_node("route_after_agents", route_after_agents)
    builder.add_node("report_writer", overrides.get("report_writer", report_writer_agent))
    builder.add_node("route_after_report", route_after_report)

    builder.add_edge(START, "supervisor")
    # supervisor returns Command([Send(financial_agent), Send(web_research_agent)])
    # LangGraph runs both in the same superstep and merges state before proceeding.
    builder.add_edge("financial_agent", "route_after_agents")
    builder.add_edge("web_research_agent", "route_after_agents")
    # route_after_agents returns Command(goto="report_writer")
    builder.add_edge("report_writer", "route_after_report")
    # route_after_report returns Command(goto="__end__")

    return builder.compile(checkpointer=checkpointer)


@asynccontextmanager
async def sqlite_graph(db_path: str = "checkpoints.db"):
    """Async context manager that yields a compiled graph backed by AsyncSqliteSaver."""
    async with AsyncSqliteSaver.from_conn_string(db_path) as checkpointer:
        yield build_graph(checkpointer=checkpointer)
