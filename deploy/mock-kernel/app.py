from __future__ import annotations

import json
import os
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse


app = FastAPI(
    title="FLARE Kernel Mock",
    version="0.1.0",
    description="Stable mock kernel for xiaocai deployment and acceptance checks",
)


class ChatRequest(BaseModel):
    user_id: str | None = Field(default=None)
    message: str
    session_id: str
    context: dict[str, Any] = Field(default_factory=dict)


def _build_run_response(request: ChatRequest) -> dict[str, Any]:
    return {
        "message": f"已收到：{request.message}",
        "session_id": request.session_id,
        "cards": [
            {
                "type": "mock-reply",
                "data": {
                    "user_id": request.user_id,
                    "message": request.message,
                    "context": request.context,
                },
            }
        ],
        "metadata": {
            "service": "flare-kernel-mock",
            "domain_pack_root": os.getenv("DOMAIN_PACK_ROOT", "/domain-pack"),
        },
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "flare-kernel-mock"}


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "service": "flare-kernel-mock",
        "endpoints": {
            "chat_run": "/chat/run",
            "chat_stream": "/chat/stream",
            "health": "/health",
        },
    }


@app.post("/chat/run")
async def chat_run(request: ChatRequest) -> dict[str, Any]:
    return _build_run_response(request)


@app.post("/run")
async def run_alias(request: ChatRequest) -> dict[str, Any]:
    return _build_run_response(request)


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    async def event_stream() -> AsyncGenerator[str, None]:
        chunks = [
            {"type": "token", "content": f"已收到：{request.message}"},
            {"type": "token", "content": "（mock kernel）"},
            {"type": "done", "session_id": request.session_id},
        ]

        for chunk in chunks:
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/stream")
async def stream_alias(request: ChatRequest) -> StreamingResponse:
    return await chat_stream(request)
