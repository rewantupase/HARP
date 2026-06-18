"""Hybrid retrieval: BGE dense + BM25 sparse → RRF → cross-encoder rerank."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID
from sqlalchemy.orm import Session
from app.config import settings
from app.database.documents import get_chunks_by_ids, get_surrounding_chunks
from app.database.session import get_session
from app.retrieval.dense import embed_query
from app.retrieval.sparse import BM25Index
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.reranker import rerank
from app.retrieval.queries import semantic_search
from app.retrieval.types import RankedChunkHit, RetrievedPassage, SearchFilters


class DocumentRetriever:
    def search(
        self,
        query: str,
        *,
        filters: SearchFilters | None = None,
        top_k: int | None = None,
        candidate_k: int | None = None,
        include_neighbors: bool = True,
        session: Session | None = None,
    ) -> list[RetrievedPassage]:
        resolved_top_k = top_k or settings.retrieval_top_k
        resolved_candidate_k = candidate_k or settings.retrieval_candidate_k
        if session is not None:
            return self._search_with_session(
                session, query, filters=filters,
                top_k=resolved_top_k, candidate_k=resolved_candidate_k,
                include_neighbors=include_neighbors,
            )
        with get_session() as s:
            return self._search_with_session(
                s, query, filters=filters,
                top_k=resolved_top_k, candidate_k=resolved_candidate_k,
                include_neighbors=include_neighbors,
            )

    def _search_with_session(
        self, session, query, *, filters, top_k, candidate_k, include_neighbors
    ) -> list[RetrievedPassage]:
        with ThreadPoolExecutor(max_workers=2) as prep:
            embed_future = prep.submit(embed_query, query)
            query_vec = embed_future.result()

        semantic_hits = semantic_search(session, query_vec, limit=candidate_k, filters=filters)
        doc_ids = filters.document_ids if filters else None
        bm25_index = BM25Index.build(session, document_ids=doc_ids)
        bm25_hits = bm25_index.search(query, limit=candidate_k)

        semantic_ids = [h.chunk_id for h in semantic_hits]
        bm25_ids = [h.chunk_id for h in bm25_hits]
        fused = reciprocal_rank_fusion([semantic_ids, bm25_ids], k=settings.retrieval_rrf_k)[:candidate_k]

        if not fused:
            return []

        fused_ids = [cid for cid, _ in fused]
        fusion_scores = {cid: score for cid, score in fused}
        chunks_by_id = get_chunks_by_ids(session, fused_ids)

        passages: list[RetrievedPassage] = []
        seen_neighbor_ids: set[UUID] = set(fused_ids)

        for chunk_id in fused_ids:
            chunk = chunks_by_id.get(chunk_id)
            if chunk is None or chunk.document is None:
                continue
            neighbors: list[RetrievedPassage] = []
            if include_neighbors:
                for nc in get_surrounding_chunks(session, chunk_id, settings.retrieval_neighbor_radius):
                    if nc.id in seen_neighbor_ids or nc.document is None:
                        continue
                    seen_neighbor_ids.add(nc.id)
                    neighbors.append(_passage_from_chunk(nc, nc.document, fusion_score=0.0))
            passages.append(
                _passage_from_chunk(chunk, chunk.document,
                                    fusion_score=fusion_scores[chunk_id],
                                    neighbors=neighbors)
            )

        return rerank(query, passages, top_k=top_k)


def _passage_from_chunk(chunk, document, *, fusion_score, neighbors=None):
    return RetrievedPassage(
        chunk_id=chunk.id,
        document_id=chunk.document_id,
        chunk_index=chunk.chunk_index,
        text=chunk.text,
        page=chunk.page,
        section=chunk.section,
        fusion_score=fusion_score,
        ticker=document.ticker,
        company_name=document.company_name,
        form=document.form,
        filing_date=document.filing_date,
        fiscal_year=document.fiscal_year,
        accession_number=document.accession_number,
        neighbors=neighbors or [],
    )
