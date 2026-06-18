"""MCP tool: search documents."""
from __future__ import annotations


async def document_search(query: str, top_k: int = 5) -> list[dict]:
    """Search the HARP knowledge base for relevant document passages."""
    from app.retrieval.retriever import DocumentRetriever
    from app.database.session import get_session
    retriever = DocumentRetriever()
    top_k = min(top_k, 20)
    with get_session() as session:
        passages = retriever.search(query, top_k=top_k, session=session)
    return [{"chunk_id": str(p.chunk_id), "document_id": str(p.document_id), "text": p.text,
             "ticker": p.ticker, "company_name": p.company_name, "form": p.form,
             "filing_date": str(p.filing_date), "page": p.page, "section": p.section,
             "fusion_score": p.fusion_score, "rerank_score": p.rerank_score} for p in passages]
