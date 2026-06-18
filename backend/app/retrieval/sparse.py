"""BM25 retrieval using rank_bm25."""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID
from rank_bm25 import BM25Okapi
from sqlalchemy.orm import Session
from app.retrieval.types import RankedChunkHit

if TYPE_CHECKING:
    pass


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


@dataclass
class BM25Index:
    chunk_ids: list[UUID]
    bm25: BM25Okapi

    @classmethod
    def build(cls, session: Session, document_ids: list[UUID] | None = None) -> "BM25Index":
        from app.database.models.document_chunk import DocumentChunk
        from sqlalchemy import select
        stmt = select(DocumentChunk.id, DocumentChunk.text)
        if document_ids:
            stmt = stmt.where(DocumentChunk.document_id.in_(document_ids))
        rows = session.execute(stmt).all()
        ids = [row.id for row in rows]
        corpus = [_tokenize(row.text) for row in rows]
        return cls(chunk_ids=ids, bm25=BM25Okapi(corpus))

    def search(self, query: str, limit: int = 50) -> list[RankedChunkHit]:
        tokens = _tokenize(query)
        scores = self.bm25.get_scores(tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: -scores[i])[:limit]
        hits = []
        for idx in top_indices:
            if scores[idx] > 0:
                hits.append(RankedChunkHit(chunk_id=self.chunk_ids[idx], score=float(scores[idx])))
        return hits
