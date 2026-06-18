"""MCP resources."""
from __future__ import annotations


async def list_document_collections() -> list[dict]:
    from app.database.session import get_session
    from app.database.models.source_document import SourceDocument
    from sqlalchemy import select, func, distinct
    with get_session() as session:
        rows = session.execute(
            select(SourceDocument.ticker, SourceDocument.company_name,
                   func.count(SourceDocument.id).label("doc_count"))
            .group_by(SourceDocument.ticker, SourceDocument.company_name)
        ).all()
    return [{"ticker": r.ticker, "company_name": r.company_name, "doc_count": r.doc_count} for r in rows]


async def get_ingestion_status() -> dict:
    return {"status": "idle", "message": "No active ingestion jobs."}


async def get_knowledge_base_metadata() -> dict:
    from app.database.session import get_session
    from app.database.models.source_document import SourceDocument
    from app.database.models.document_chunk import DocumentChunk
    from sqlalchemy import select, func
    with get_session() as session:
        doc_count = session.execute(select(func.count(SourceDocument.id))).scalar()
        chunk_count = session.execute(select(func.count(DocumentChunk.id))).scalar()
    return {"document_count": doc_count, "chunk_count": chunk_count}
