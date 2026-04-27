"""
Demo standalone FastAPI host for the agent.

Three lines of glue. Lets us run the agent as its own service for end-to-
end testing:

    uvicorn agent.app:app --host 127.0.0.1 --port 8002

The production FastAPI app does the same `include_router` in its own
codebase — this file exists so we can verify the plug-in pattern works
in isolation, without coupling the agent to the existing `mcp_server`
FastAPI app (they're conceptually different services: one is an MCP
server, the other is an MCP client).
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from agent.api import router

app = FastAPI(title="Agent Service", description="MCP-backed agent over SSE.")


def _custom_openapi() -> dict:
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema.setdefault("components", {})
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {"type": "http", "scheme": "bearer"}
    }
    for path in schema.get("paths", {}).values():
        for operation in path.values():
            operation["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema


app.openapi = _custom_openapi  # type: ignore[method-assign]
app.include_router(router)
