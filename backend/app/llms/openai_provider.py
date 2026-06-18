"""OpenAI provider — fallback and grounding model."""
from __future__ import annotations
import time
from typing import AsyncIterator
from openai import OpenAI, AsyncOpenAI
from app.llms.base import BaseLLMProvider, GenerateResponse
from app.config import settings


class OpenAIProvider(BaseLLMProvider):
    name = "openai"

    def __init__(self, model: str | None = None) -> None:
        self._model = model or settings.openai_chat_model

    def generate(self, prompt: str, system: str | None = None) -> GenerateResponse:
        t0 = time.perf_counter()
        client = OpenAI(api_key=settings.openai_api_key)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(model=self._model, messages=messages, temperature=0.0)
        usage = resp.usage
        return GenerateResponse(text=resp.choices[0].message.content or "",
                                model=self._model,
                                input_tokens=usage.prompt_tokens if usage else 0,
                                output_tokens=usage.completion_tokens if usage else 0,
                                latency_ms=int((time.perf_counter() - t0) * 1000))

    async def stream(self, prompt: str, system: str | None = None) -> AsyncIterator[str]:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        async with client.chat.completions.stream(model=self._model, messages=messages) as stream:
            async for event in stream:
                if event.choices and event.choices[0].delta.content:
                    yield event.choices[0].delta.content

    def health_check(self) -> bool:
        try:
            OpenAI(api_key=settings.openai_api_key).models.list()
            return True
        except Exception:
            return False
