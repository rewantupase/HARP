"""Local dense embeddings using bge-small-en-v1.5 via sentence-transformers."""
from __future__ import annotations
from functools import lru_cache
from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-small-en-v1.5"
DIMENSIONS = 384


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_query(text: str) -> list[float]:
    prefixed = f"Represent this sentence for searching relevant passages: {text}"
    vec = _model().encode(prefixed, normalize_embeddings=True)
    return vec.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    vecs = _model().encode(texts, normalize_embeddings=True, batch_size=64)
    return [v.tolist() for v in vecs]
