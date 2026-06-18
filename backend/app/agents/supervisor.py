"""Supervisor agent."""
from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID
import structlog
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.citation_agent import CitationAgent
from app.agents.memory_agent import MemoryAgent
from app.retrieval.retriever import DocumentRetriever
from app.retrieval.types import RetrievedPassage
from app.llms.router import route, RoutingDecision
from app.llms.provider_factory import get_provider

logger = structlog.get_logger()


@dataclass
class SupervisorResult:
    answer: str
    passages: list[RetrievedPassage]
    routing: RoutingDecision
    citations: list[dict]
    memory_context_used: bool


class SupervisorAgent:
    def __init__(self, retriever: DocumentRetriever, thread_id: UUID, user_id: UUID,
                 model_hint: str | None = None) -> None:
        self.retriever = retriever
        self.thread_id = thread_id
        self.user_id = user_id
        self.model_hint = model_hint
        self._retrieval = RetrievalAgent(retriever)
        self._citation = CitationAgent()
        self._memory = MemoryAgent(thread_id=thread_id, user_id=user_id)

    def run(self, query: str) -> SupervisorResult:
        logger.info("supervisor.start", query=query[:80])
        memory_context = self._memory.retrieve(query)
        augmented_query = f"{memory_context}\n\nUser question: {query}" if memory_context else query
        passages = self._retrieval.retrieve(augmented_query)
        logger.info("supervisor.retrieved", count=len(passages))
        decision = route(query, passages, model_hint=self.model_hint)
        logger.info("supervisor.routed", provider=decision.provider_name, tier=decision.tier)
        provider = get_provider(decision.provider_name)
        system = _build_system_prompt(passages, memory_context)
        response = provider.generate(query, system=system)
        verified_citations = self._citation.verify(response.text, passages)
        self._memory.append(role="user", content=query)
        self._memory.append(role="assistant", content=response.text,
                            model_used=decision.provider_name, latency_ms=response.latency_ms)
        return SupervisorResult(answer=response.text, passages=passages, routing=decision,
                                citations=verified_citations, memory_context_used=bool(memory_context))


def _build_system_prompt(passages: list[RetrievedPassage], memory_context: str) -> str:
    context_parts = [f"[{i+1}] {p.text}" for i, p in enumerate(passages)]
    context = "\n\n".join(context_parts)
    prompt = ("You are HARP, an AI document intelligence assistant. "
              "Answer the user's question using ONLY the provided context. "
              "Cite sources using [1], [2], etc. matching the context numbers. "
              "If the answer is not in the context, say so clearly.\n\n"
              f"Context:\n{context}")
    if memory_context:
        prompt = f"{memory_context}\n\n{prompt}"
    return prompt
