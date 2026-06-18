"""MCP tool: trigger document ingestion."""
from __future__ import annotations


async def document_upload(ticker: str, form: str, source_url: str, fiscal_year: int | None = None) -> dict:
    """Ingest a new document into HARP from a URL."""
    return {"status": "queued", "ticker": ticker.upper(), "form": form.upper(),
            "source_url": source_url, "fiscal_year": fiscal_year,
            "message": "Document ingestion queued. Check harp://ingestion-status for updates."}
