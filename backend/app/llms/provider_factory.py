"""Factory that instantiates and caches LLM providers."""
from __future__ import annotations
from functools import lru_cache
from app.llms.base import BaseLLMProvider


@lru_cache(maxsize=1)
def get_phi3() -> BaseLLMProvider:
    from app.llms.phi3 import Phi3Provider
    return Phi3Provider()


@lru_cache(maxsize=1)
def get_mistral() -> BaseLLMProvider:
    from app.llms.mistral import MistralProvider
    return MistralProvider()


@lru_cache(maxsize=1)
def get_llama3() -> BaseLLMProvider:
    from app.llms.llama3 import Llama3Provider
    return Llama3Provider()


@lru_cache(maxsize=1)
def get_openai(model: str | None = None) -> BaseLLMProvider:
    from app.llms.openai_provider import OpenAIProvider
    return OpenAIProvider(model=model)


def get_provider(name: str) -> BaseLLMProvider:
    mapping = {"phi3": get_phi3, "mistral": get_mistral, "llama3": get_llama3, "openai": get_openai}
    if name not in mapping:
        raise ValueError(f"Unknown provider: {name}. Choose from {list(mapping)}")
    return mapping[name]()
