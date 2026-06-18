"""Structured latency and quality metrics."""
from __future__ import annotations
import structlog

logger = structlog.get_logger()


def log_retrieval_metrics(query: str, retrieval_latency_ms: int, passage_count: int,
                           top_rerank_score: float | None) -> None:
    logger.info("metrics.retrieval", query_preview=query[:60], latency_ms=retrieval_latency_ms,
                passage_count=passage_count, top_rerank_score=top_rerank_score)


def log_generation_metrics(model: str, tier: str, latency_ms: int, input_tokens: int,
                            output_tokens: int, citation_count: int) -> None:
    logger.info("metrics.generation", model=model, tier=tier, latency_ms=latency_ms,
                input_tokens=input_tokens, output_tokens=output_tokens, citation_count=citation_count)


def log_memory_metrics(conversation_id: str, memory_chars: int, summary_used: bool) -> None:
    logger.info("metrics.memory", conversation_id=conversation_id, memory_chars=memory_chars,
                summary_used=summary_used)
