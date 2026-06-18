"""LangSmith tracing integration."""
from __future__ import annotations
import os, time
from contextlib import contextmanager
from typing import Any, Generator
import structlog

logger = structlog.get_logger()
_LANGSMITH_ENABLED = bool(os.getenv("LANGCHAIN_API_KEY"))


@contextmanager
def trace_run(name: str, run_type: str = "chain", metadata: dict[str, Any] | None = None) -> Generator[dict, None, None]:
    run: dict[str, Any] = {"name": name, "metadata": metadata or {}}
    t0 = time.perf_counter()
    if _LANGSMITH_ENABLED:
        try:
            from langsmith import Client
            run["_client"] = Client()
        except ImportError:
            pass
    try:
        yield run
    finally:
        elapsed = int((time.perf_counter() - t0) * 1000)
        run["latency_ms"] = elapsed
        logger.info("trace.run_complete", name=name, latency_ms=elapsed,
                    **{k: v for k, v in (metadata or {}).items() if isinstance(v, (str, int, float))})
