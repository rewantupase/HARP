# HARP — AI Document Intelligence Platform

Built on top of Document Copilot. See `HARP_Implementation_Plan.md` for full details.

## What's new vs Document Copilot

| Capability | Before | After |
|---|---|---|
| Embeddings | OpenAI (cloud) | BGE-small-en-v1.5 (local, free) |
| Sparse retrieval | PostgreSQL FTS | BM25 (rank_bm25) |
| Reranking | None | Cross-encoder (ms-marco-MiniLM-L-6-v2) |
| LLM providers | OpenAI only | Phi-3, Mistral 7B, Llama 3 8B + OpenAI fallback |
| Model routing | None | Confidence-based 3-tier router |
| Conversation memory | None | PostgreSQL-backed with auto-summarization |
| MCP server | None | Native (Claude Desktop, Cursor, VS Code) |
| Agent architecture | Single agent | Supervisor + Retrieval + Citation + Memory agents |
| Observability | structlog | LangSmith + structured metrics |

## Quick Start

```bash
# 1. Pull Ollama models (~15GB disk)
bash backend/scripts/setup_ollama.sh

# 2. Install new Python deps
cd backend && uv sync

# 3. Run migration
alembic upgrade head

# 4. Re-embed existing chunks (embedding dim changed 1536→384)
python scripts/reembed_chunks.py

# 5. Start services
docker compose up
```

## MCP (Claude Desktop)

Copy `docs/claude_desktop_config.json` to:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

## New Files

```
backend/app/
├── agents/          supervisor, retrieval, citation, memory agents
├── llms/            phi3, mistral, llama3, openai providers + router
├── mcp/             native MCP server + 4 tools + 3 resources
├── observability/   LangSmith tracing + metrics
└── retrieval/
    ├── dense.py     BGE-small-en-v1.5 embeddings
    ├── sparse.py    BM25 (rank_bm25)
    └── reranker.py  cross-encoder reranker
```
