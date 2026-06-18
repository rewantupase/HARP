"""Confidence-based model router."""
from __future__ import annotations
import re
from dataclasses import dataclass
from enum import Enum
import structlog
from app.llms.base import BaseLLMProvider
from app.retrieval.types import RetrievedPassage

logger = structlog.get_logger()


class RoutingTier(str, Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    FALLBACK = "fallback"


@dataclass
class RoutingDecision:
    tier: RoutingTier
    provider_name: str
    reason: str


def _estimate_complexity(query: str) -> float:
    word_count = len(query.split())
    has_comparison = bool(re.search(r"\bvs\b|compar|differ|between|versus", query, re.I))
    has_multi_step = bool(re.search(r"\band\b.*\band\b|first.*then|both", query, re.I))
    has_reasoning = bool(re.search(r"\bwhy\b|\bhow\b|explain|reason|cause|imply", query, re.I))
    question_count = query.count("?")
    score = 0.0
    score += min(word_count / 40.0, 0.3)
    score += 0.25 if has_comparison else 0.0
    score += 0.2 if has_multi_step else 0.0
    score += 0.15 if has_reasoning else 0.0
    score += min(question_count * 0.05, 0.1)
    return min(score, 1.0)


def _retrieval_confidence(passages: list[RetrievedPassage]) -> float:
    scores = [p.rerank_score for p in passages if p.rerank_score is not None]
    return max(scores, default=0.0)


def _context_tokens(passages: list[RetrievedPassage]) -> int:
    return sum(len(p.text.split()) * 4 // 3 for p in passages)


def route(query: str, passages: list[RetrievedPassage], model_hint: str | None = None) -> RoutingDecision:
    from app.llms.provider_factory import get_provider
    if model_hint:
        return RoutingDecision(tier=RoutingTier.FALLBACK, provider_name=model_hint,
                               reason=f"explicit client hint: {model_hint}")
    complexity = _estimate_complexity(query)
    confidence = _retrieval_confidence(passages)
    ctx_tokens = _context_tokens(passages)
    if ctx_tokens > 4000:
        tier = RoutingTier.COMPLEX
    elif complexity >= 0.6:
        tier = RoutingTier.COMPLEX
    elif complexity >= 0.3 or confidence < 0.3:
        tier = RoutingTier.MEDIUM
    else:
        tier = RoutingTier.SIMPLE
    tier_providers = {RoutingTier.SIMPLE: "phi3", RoutingTier.MEDIUM: "mistral", RoutingTier.COMPLEX: "llama3"}
    provider_name = tier_providers.get(tier, "openai")
    try:
        provider = get_provider(provider_name)
        if not provider.health_check():
            raise RuntimeError(f"{provider_name} unhealthy")
    except Exception as e:
        logger.warning("router_fallback", provider=provider_name, reason=str(e))
        provider_name = "openai"
        tier = RoutingTier.FALLBACK
    reason = (f"complexity={complexity:.2f}, confidence={confidence:.2f}, "
              f"ctx_tokens={ctx_tokens}, tier={tier.value}")
    logger.info("router_decision", provider=provider_name, reason=reason)
    return RoutingDecision(tier=tier, provider_name=provider_name, reason=reason)
