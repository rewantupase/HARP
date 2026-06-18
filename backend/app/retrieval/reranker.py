"""Cross-encoder reranker using ms-marco-MiniLM-L-6-v2."""
from __future__ import annotations
from functools import lru_cache
from sentence_transformers import CrossEncoder
from app.retrieval.types import RetrievedPassage

MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


@lru_cache(maxsize=1)
def _model() -> CrossEncoder:
    return CrossEncoder(MODEL_NAME)


def rerank(query: str, passages: list[RetrievedPassage], top_k: int = 10) -> list[RetrievedPassage]:
    if not passages:
        return []
    pairs = [(query, p.text) for p in passages]
    scores = _model().predict(pairs, show_progress_bar=False)
    scored = sorted(zip(passages, scores), key=lambda x: -x[1])
    result = []
    for passage, score in scored[:top_k]:
        result.append(passage.model_copy(update={"rerank_score": float(score)}))
    return result
