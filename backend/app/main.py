from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.memory import router as memory_router
from app.config import settings
from app.mcp.server import mcp

app = FastAPI(title="HARP")
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(memory_router)

# Mount MCP server at /mcp (SSE transport)
app.mount("/mcp", mcp.get_asgi_app())

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/mcp")
async def health_mcp() -> dict[str, bool]:
    tools = ["document_search", "document_upload", "chat_history_lookup", "document_metadata_lookup"]
    return {t: True for t in tools}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000)
