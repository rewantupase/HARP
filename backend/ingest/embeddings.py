"""Ingest-time embeddings: delegates to local bge-small-en-v1.5."""
from app.retrieval.dense import embed_texts


def embed_chunks(texts: list[str]) -> list[list[float]]:
    """Embed a batch of document chunks for storage."""
    return embed_texts(texts)
