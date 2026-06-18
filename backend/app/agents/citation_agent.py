"""Citation agent: verify cited passages."""
from __future__ import annotations
import re
import structlog
from app.retrieval.types import RetrievedPassage

logger = structlog.get_logger()


class CitationAgent:
    def verify(self, answer: str, passages: list[RetrievedPassage]) -> list[dict]:
        refs = set(int(m) for m in re.findall(r"\[(\d+)\]", answer))
        citations = []
        for ref in sorted(refs):
            idx = ref - 1
            if 0 <= idx < len(passages):
                p = passages[idx]
                citations.append({"citation_index": ref, "chunk_id": str(p.chunk_id),
                                   "document_id": str(p.document_id), "text_snippet": p.text[:200],
                                   "ticker": p.ticker, "form": p.form, "filing_date": str(p.filing_date),
                                   "page": p.page, "section": p.section, "rerank_score": p.rerank_score})
                logger.info("citation_agent.verified", ref=ref, ticker=p.ticker)
            else:
                logger.warning("citation_agent.out_of_range", ref=ref)
        return citations
