"""Native MCP server for HARP."""
from __future__ import annotations
from mcp.server.fastmcp import FastMCP
from app.mcp.tools.document_search import document_search
from app.mcp.tools.document_upload import document_upload
from app.mcp.tools.chat_history import chat_history_lookup
from app.mcp.tools.document_metadata import document_metadata_lookup
from app.mcp.resources.collections import (list_document_collections,
                                            get_ingestion_status, get_knowledge_base_metadata)

mcp = FastMCP("HARP Document Intelligence")

mcp.tool()(document_search)
mcp.tool()(document_upload)
mcp.tool()(chat_history_lookup)
mcp.tool()(document_metadata_lookup)


@mcp.resource("harp://collections")
async def collections_resource() -> str:
    import json
    return json.dumps(await list_document_collections(), default=str)


@mcp.resource("harp://ingestion-status")
async def ingestion_status_resource() -> str:
    import json
    return json.dumps(await get_ingestion_status(), default=str)


@mcp.resource("harp://knowledge-base")
async def knowledge_base_resource() -> str:
    import json
    return json.dumps(await get_knowledge_base_metadata(), default=str)
