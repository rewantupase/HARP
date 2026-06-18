"""Abstract base class for all LLM providers."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator


@dataclass
class GenerateResponse:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


class BaseLLMProvider(ABC):
    name: str

    @abstractmethod
    def generate(self, prompt: str, system: str | None = None) -> GenerateResponse: ...

    @abstractmethod
    async def stream(self, prompt: str, system: str | None = None) -> AsyncIterator[str]: ...

    @abstractmethod
    def health_check(self) -> bool: ...
