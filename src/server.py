import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

from src.graph import sqlite_graph


class ResearchRequest(BaseModel):
    query: str
    thread_id: Optional[str] = None


class ResearchResponse(BaseModel):
    thread_id: str
    report: str


_graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _graph
    async with sqlite_graph() as g:
        _graph = g
        yield


app = FastAPI(lifespan=lifespan)


@app.post("/research", response_model=ResearchResponse)
async def research(req: ResearchRequest) -> ResearchResponse:
    thread_id = req.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    result = await _graph.ainvoke(
        {"query": req.query, "thread_id": thread_id},
        config=config,
    )

    return ResearchResponse(thread_id=thread_id, report=result["report"])
