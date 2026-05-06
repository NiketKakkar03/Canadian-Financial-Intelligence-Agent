# Canadian Financial Intelligence Agent

A multi-agent LangGraph system that accepts a natural-language research query about a TSX-listed company, autonomously delegates to specialized agents running in parallel, and returns a structured Markdown investment brief via a FastAPI HTTP endpoint.

Built as a portfolio piece targeting Canadian fintech roles (RBC, Manulife, TD, AWS Canada). Demonstrates MultiServerMCPClient connecting to two live MCP servers simultaneously, parallel agent execution via the LangGraph Send API, and SQLite-backed checkpointing.

> **Depends on** [TSX Financial Data MCP Server](https://github.com/NiketKakkar03/TSX-Financial-Data-MCP-Server) — a FastMCP server exposing structured quarterly financials for TSX 60 companies via `search_filings` and `summarize_quarter` tools.

## Architecture

```
POST /research
      │
      ▼
 Supervisor ──── Send API ────┬─── Financial Agent ──► TSX MCP Server (Project 1)
                              │                         search_filings + summarize_quarter
                              └─── Web Research Agent ► Tavily MCP Server (Docker)
                                                        live analyst commentary + news
                              │
                              ▼
                        Report Writer
                        4-section Markdown brief
                              │
                              ▼
                    JSON response (thread_id + report)
```

| Server | Transport | URL |
|---|---|---|
| TSX Financial Data (Project 1) | streamable-http | `http://localhost:8000/mcp` |
| Tavily (Docker) | SSE | `http://localhost:8001/mcp` |

## Prerequisites

- Python 3.10
- Docker Desktop
- [TSX Financial Data MCP Server](https://github.com/NiketKakkar03/TSX-Financial-Data-MCP-Server) with its Postgres container running
- Anthropic API key — [console.anthropic.com](https://console.anthropic.com)
- Tavily API key — [tavily.com](https://tavily.com)

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # fill in ANTHROPIC_API_KEY and TAVILY_API_KEY
```

## Starting the system

Run each in a separate terminal, in order.

**1. Tavily MCP server (Docker):**
```bash
docker compose up -d
```

**2. Financial MCP server (Project 1) — PowerShell:**
```powershell
$env:DATABASE_URL = "postgresql://tsx:tsx@localhost:5433/tsx"
$env:PYTHONPATH = "C:\Users\niket\OneDrive\Desktop\Programming\Projects\TSX-Financial-Data-MCP-Server"
$env:MCP_TRANSPORT = "streamable-http"
python C:\Users\niket\OneDrive\Desktop\Programming\Projects\TSX-Financial-Data-MCP-Server\src\server.py
```

**3. API server:**
```bash
export $(cat .env | grep -v '^#' | xargs) && uvicorn src.server:app --reload --port 8080
```

## Usage

```bash
curl -X POST http://localhost:8080/research \
  -H "Content-Type: application/json" \
  -d '{"query": "Summarise RBC Q4 2024 results and analyst sentiment"}'
```

**Request body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `query` | string | yes | Natural-language research question |
| `thread_id` | string (UUID) | no | Supply to resume a checkpointed run; omit to start fresh |

**Response body:**

| Field | Type | Description |
|---|---|---|
| `thread_id` | string | UUID for this run — store it to resume later |
| `report` | string | Structured Markdown investment brief |

**Example response:**
```json
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "report": "## Revenue Trend\n...\n## Profitability Analysis\n...\n## Analyst Sentiment\n...\n## Risk Summary\n..."
}
```

## Graceful degradation

If the TSX Financial Data MCP server is unreachable, the system still returns a report. The financial sections include a visible notice that structured data was unavailable, and the brief is populated from Tavily web research alone.

## Testing

```bash
# Unit + integration tests (no live servers needed)
pytest tests/test_state.py tests/test_supervisor.py tests/test_graph.py -v

# MCP client integration test (requires both MCP servers running)
pytest tests/test_mcp_client.py -v
```

## Project structure

```
src/
  state.py              — typed ResearchState dataclass shared across all agents
  mcp_client.py         — all MultiServerMCPClient wiring; exposes get_mcp_tools()
  graph.py              — LangGraph topology (build_graph(), sqlite_graph())
  server.py             — FastAPI layer (POST /research)
  agents/
    supervisor.py       — fan-out via Send API, completeness check, routing
    financial.py        — calls summarize_quarter + search_filings
    web_research.py     — calls Tavily search tools
    report_writer.py    — synthesizes 4-section Markdown brief
tests/
  test_state.py         — ResearchState initialization and partial state validity
  test_supervisor.py    — all routing branches with mocked agent nodes
  test_graph.py         — end-to-end graph with mocked nodes + thread isolation
  test_mcp_client.py    — live integration test for get_mcp_tools()
docker-compose.yml      — Tavily MCP server (supergateway + tavily-mcp, SSE)
```

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | yes | Anthropic API key for Claude |
| `TAVILY_API_KEY` | yes | Tavily API key (passed to Docker service) |
| `FINANCIAL_MCP_URL` | no | Financial MCP server URL (default: `http://localhost:8000/mcp`) |
| `TAVILY_MCP_URL` | no | Tavily MCP server URL (default: `http://localhost:8001/mcp`) |
| `ANTHROPIC_MODEL` | no | Claude model to use (default: `claude-haiku-4-5-20251001`) |
