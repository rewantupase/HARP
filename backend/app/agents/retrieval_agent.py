"""Retrieval agent."""
from __future__ import annotations
import structlog
from app.retrieval.retriever import DocumentRetriever
from app.retrieval.types import RetrievedPassage, SearchFilters

logger = structlog.get_logger()


class RetrievalAgent:
    def __init__(self, retriever: DocumentRetriever) -> None:
        self._retriever = retriever

    def retrieve(self, query: str, filters: SearchFilters | None = None, top_k: int = 10) -> list[RetrievedPassage]:
        passages = self._retriever.search(query, filters=filters, top_k=top_k)
        logger.info("retrieval_agent.done", top_rerank=passages[0].rerank_score if passages else None, count=len(passages))
        return passages
