"""MCP tool: look up document metadata."""
from __future__ import annotations


async def document_metadata_lookup(ticker: str | None = None, form: str | None = None,
                                    fiscal_year: int | None = None) -> list[dict]:
    """Look up source document metadata."""
    from app.database.session import get_session
    from app.database.models.source_document import SourceDocument
    from sqlalchemy import select
    with get_session() as session:
        stmt = select(SourceDocument)
        if ticker:
            stmt = stmt.where(SourceDocument.ticker == ticker.upper())
        if form:
            stmt = stmt.where(SourceDocument.form == form.upper())
        if fiscal_year:
            stmt = stmt.where(SourceDocument.fiscal_year == fiscal_year)
        docs = session.execute(stmt.limit(50)).scalars().all()
    return [{"id": str(d.id), "ticker": d.ticker, "company_name": d.company_name,
             "form": d.form, "filing_date": str(d.filing_date), "fiscal_year": d.fiscal_year,
             "accession_number": d.accession_number, "source_url": d.source_url} for d in docs]
