"""Mistral 7B provider via Ollama."""
from __future__ import annotations
import time, json
from typing import AsyncIterator
import httpx
from app.llms.base import BaseLLMProvider, GenerateResponse
from app.config import settings


class MistralProvider(BaseLLMProvider):
    name = "mistral"
    _model_tag = "mistral:7b"

    def generate(self, prompt: str, system: str | None = None) -> GenerateResponse:
        t0 = time.perf_counter()
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = httpx.post(f"{settings.ollama_base_url}/api/chat",
                          json={"model": self._model_tag, "messages": messages, "stream": False},
                          timeout=180)
        resp.raise_for_status()
        data = resp.json()
        return GenerateResponse(text=data["message"]["content"], model=self._model_tag,
                                input_tokens=data.get("prompt_eval_count", 0),
                                output_tokens=data.get("eval_count", 0),
                                latency_ms=int((time.perf_counter() - t0) * 1000))

    async def stream(self, prompt: str, system: str | None = None) -> AsyncIterator[str]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        async with httpx.AsyncClient(timeout=180) as client:
            async with client.stream("POST", f"{settings.ollama_base_url}/api/chat",
                                     json={"model": self._model_tag, "messages": messages, "stream": True}) as resp:
                async for line in resp.aiter_lines():
                    if line:
                        chunk = json.loads(line)
                        if token := chunk.get("message", {}).get("content", ""):
                            yield token
                        if chunk.get("done"):
                            break

    def health_check(self) -> bool:
        try:
            resp = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=5)
            data = resp.json()
            return any(m["name"].startswith("mistral") for m in data.get("models", []))
        except Exception:
            return False
