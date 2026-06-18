# HARP — AI Document Intelligence Platform

HARP is a production-grade RAG application that lets analysts query SEC filings (10-Ks, 10-Qs) in plain English and receive grounded, citable answers. It is built on top of a Document Copilot core and extends it with a multi-agent architecture, local LLM support via Ollama, confidence-based model routing, conversation memory, a native MCP server, and LangSmith observability.

---

## What's New vs. Document Copilot

| Capability |  |
|---|---|
| Embeddings | `BGE-small-en-v1.5` (local, free) |
| Sparse retrieval | BM25 (`rank_bm25`) |
| Reranking | Cross-encoder (`ms-marco-MiniLM-L-6-v2`) |
| LLM providers | Phi-3, Mistral 7B, Llama 3 8B + OpenAI fallback |
| Model routing | Confidence-based 3-tier router |
| Conversation memory | PostgreSQL-backed with auto-summarization |
| MCP server | Native (Claude Desktop, Cursor, VS Code) |
| Agent architecture | Supervisor + Retrieval + Citation + Memory agents |
| Observability | LangSmith tracing + structured metrics |

---

## Stack

| Layer | Choice |
|---|---|
| Frontend | Vite + React SPA + TypeScript, Tailwind CSS, shadcn/ui |
| Backend | Python 3.12+, FastAPI, PydanticAI |
| Database | Supabase Postgres (pgvector + FTS) |
| Migrations | SQLAlchemy models + Alembic |
| Auth | Supabase Auth (email) |
| Embeddings | `BGE-small-en-v1.5` (local via `sentence-transformers`) |
| Sparse retrieval | BM25 (`rank_bm25`) |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| LLM providers | Phi-3, Mistral 7B, Llama 3 8B (Ollama) + OpenAI fallback |
| MCP | `fastmcp` — 4 tools, 3 resources |
| Observability | LangSmith + `structlog` |
| Hosting | Railway (frontend + backend), Supabase (database) |

---

## Architecture

### High-Level Service Map

```mermaid
flowchart LR
    user[Analyst] --> browser[Browser React SPA]

    subgraph railway[Railway]
        frontend[Frontend Vite and Caddy]
        backend[Backend FastAPI]
    end

    subgraph supabase[Supabase]
        auth[Auth email session]
        db[(Postgres chats and docs and chunks pgvector and FTS)]
    end

    subgraph local[Local Ollama]
        phi3[Phi-3 simple queries]
        mistral[Mistral 7B medium queries]
        llama3[Llama 3 8B complex queries]
        bge[BGE-small embeddings]
        reranker[Cross-encoder ms-marco-MiniLM]
    end

    openai[OpenAI fallback LLM]
    langsmith[LangSmith tracing]
    mcp_client[MCP client Claude Desktop and Cursor and VS Code]

    frontend -->|serves app| browser
    browser -->|sign in| auth
    auth -->|JWT| browser
    browser -->|chat with JWT| backend
    backend -->|verify user| auth
    backend -->|retrieve and persist| db
    backend -->|route query| phi3
    backend -->|route query| mistral
    backend -->|route query| llama3
    backend -->|fallback| openai
    backend -->|embed| bge
    backend -->|rerank| reranker
    backend -->|trace| langsmith
    backend -->|SSE stream| browser
    mcp_client -->|MCP protocol| backend
```

---

### Request Flow (Chat Turn)

```mermaid
sequenceDiagram
    participant B as Browser
    participant F as FastAPI
    participant S as SupervisorAgent
    participant Mem as MemoryAgent
    participant Ret as RetrievalAgent
    participant Cit as CitationAgent
    participant R as Router
    participant LLM as LLM Provider
    participant DB as Supabase Postgres

    B->>F: POST /chat/stream with JWT and message
    F->>F: Verify Supabase JWT
    F->>S: run(query)
    S->>Mem: retrieve(query) to load conversation context
    Mem->>DB: fetch recent messages and summary
    S->>Ret: retrieve(augmented_query)
    Ret->>Ret: embed with BGE-small and BM25 in parallel
    Ret->>Ret: RRF fusion
    Ret->>Ret: Cross-encoder rerank to top-k passages
    S->>R: route(query, passages) with complexity and confidence scoring
    R-->>S: RoutingDecision with tier simple/medium/complex/fallback
    S->>LLM: generate(prompt, system_with_context)
    LLM-->>S: answer text
    S->>Cit: verify(answer, passages)
    Cit-->>S: verified citations
    S->>Mem: append user and assistant messages
    Mem->>DB: persist messages and auto-summarize every 20 turns
    S-->>F: SupervisorResult
    F->>DB: persist thread and citations
    F->>B: SSE stream with text deltas and citation events
```

---

### Retrieval Pipeline

```mermaid
flowchart TD
    Q[User query] --> PREP[Parallel prep]
    PREP --> BGE[BGE-small-en-v1.5 embed query]
    PREP --> BM25[BM25 keyword extraction]

    BGE --> VEC[pgvector cosine semantic search]
    BM25 --> FTS[rank_bm25 sparse search]

    VEC -->|top candidate_k| SEM_IDS[Semantic ranked IDs]
    FTS -->|top candidate_k| BM25_IDS[BM25 ranked IDs]

    SEM_IDS --> RRF[Reciprocal Rank Fusion]
    BM25_IDS --> RRF

    RRF --> RERANK[Cross-encoder reranker ms-marco-MiniLM-L-6-v2]
    RERANK -->|top_k scored passages| HYDRATE[Hydrate chunks with document metadata]
    HYDRATE --> NEIGH[Fetch neighboring chunks for context window]
    NEIGH --> OUT[list of RetrievedPassage]
```

---

### LLM Routing

```mermaid
flowchart TD
    Q[Query and passages] --> HINT{Client model hint?}
    HINT -->|yes| DIRECT[Use hinted provider]
    HINT -->|no| SCORE[Score complexity and confidence]

    SCORE --> CTX{ctx_tokens over 4000?}
    CTX -->|yes| COMPLEX[Tier COMPLEX - Llama 3 8B]
    CTX -->|no| COMP{complexity over 0.6?}
    COMP -->|yes| COMPLEX
    COMP -->|no| MED{complexity over 0.3 or confidence under 0.3?}
    MED -->|yes| MEDIUM[Tier MEDIUM - Mistral 7B]
    MED -->|no| SIMPLE[Tier SIMPLE - Phi-3]

    COMPLEX --> HEALTH{Provider healthy?}
    MEDIUM --> HEALTH
    SIMPLE --> HEALTH
    HEALTH -->|no| FALLBACK[Fallback - OpenAI]
    HEALTH -->|yes| GENERATE[Generate answer]
```

---

### Multi-Agent Architecture

```mermaid
flowchart TD
    ORCH[Chat Orchestrator] --> SUP[SupervisorAgent]

    SUP --> MEM[MemoryAgent retrieve conversation context]
    SUP --> RET[RetrievalAgent hybrid search and rerank]
    SUP --> ROUTER[LLM Router confidence-based tier selection]
    SUP --> CIT[CitationAgent verify answer vs passages]

    MEM --> DB_MEM[(conversations and conversation_messages and conversation_summaries)]
    RET --> DB_CHUNKS[(document_chunks pgvector and BM25)]
    ROUTER --> PROVIDERS[Phi-3 and Mistral and Llama 3 and OpenAI]
    CIT --> GROUNDING[GroundingValidator citation and passage integrity]

    SUP --> RESULT[SupervisorResult answer and passages and citations and routing]
    RESULT --> ORCH
    ORCH --> STREAM[SSE stream to browser]
    ORCH --> PERSIST[(chat_threads and chat_messages and message_citations)]
```

---

### MCP Server

```mermaid
flowchart LR
    CLIENT[MCP Client Claude Desktop and Cursor and VS Code] -->|MCP protocol| SERVER[FastMCP HARP Document Intelligence]

    SERVER --> T1[document_search hybrid retrieval tool]
    SERVER --> T2[document_upload ingest new documents]
    SERVER --> T3[chat_history_lookup fetch conversation history]
    SERVER --> T4[document_metadata_lookup filing metadata]

    SERVER --> R1[harp://collections list document collections]
    SERVER --> R2[harp://ingestion-status ingestion pipeline status]
    SERVER --> R3[harp://knowledge-base knowledge base metadata]
```

---

### Data Model

```mermaid
erDiagram
    profiles ||--o{ chat_threads : owns
    chat_threads ||--o{ chat_messages : contains
    chat_messages ||--o{ message_citations : has
    message_citations }o--|| document_chunks : references
    source_documents ||--o{ document_chunks : splits_into
    profiles ||--o{ conversations : has
    conversations ||--o{ conversation_messages : contains
    conversations ||--o{ conversation_summaries : summarized_by

    profiles {
        uuid id
    }
    chat_threads {
        uuid id
        uuid user_id
        text title
    }
    chat_messages {
        uuid id
        uuid thread_id
        text role
        text content
    }
    message_citations {
        uuid id
        uuid message_id
        uuid chunk_id
    }
    source_documents {
        uuid id
        text ticker
        text form
        date filing_date
        int fiscal_year
    }
    document_chunks {
        uuid id
        uuid document_id
        int chunk_index
        text content
        vector embedding
    }
    conversations {
        uuid id
        uuid thread_id
        uuid user_id
    }
    conversation_messages {
        uuid id
        uuid conversation_id
        text role
        text content
        text model_used
        int latency_ms
    }
    conversation_summaries {
        uuid id
        uuid conversation_id
        text summary_text
    }
```

---

## Repo Layout

```text
harp/
├── backend/
│   ├── app/
│   │   ├── agents/          # supervisor, retrieval, citation, memory agents
│   │   ├── api/             # FastAPI routes (chat, auth, memory)
│   │   ├── assistant/       # PydanticAI agent, deps, outputs, instructions
│   │   ├── auth/            # Supabase JWT verification
│   │   ├── chat/            # orchestrator, streaming, message helpers
│   │   ├── database/        # SQLAlchemy models, session, Supabase client
│   │   ├── grounding/       # citation validator
│   │   ├── llms/            # phi3, mistral, llama3, openai providers + router
│   │   ├── mcp/             # FastMCP server, 4 tools, 3 resources
│   │   ├── observability/   # LangSmith tracing + metrics
│   │   └── retrieval/       # dense (BGE), sparse (BM25), reranker, RRF, types
│   ├── alembic/             # DB migrations
│   ├── ingest/              # SEC filing download, chunking, embedding pipeline
│   ├── scripts/             # smoke tests, re-embed utility, Ollama setup
│   └── tests/               # unit + integration tests
├── frontend/
│   ├── src/
│   │   ├── components/      # chat UI, citations, source passages, model selector
│   │   ├── hooks/           # useChatTransport, useSession, useThreads
│   │   ├── lib/             # api, http, citations, env, supabase client
│   │   └── pages/           # Login, SignUp, ChatThreadPage, ChatEmptyPage
│   └── Caddyfile            # production static file serving
├── data/                    # SEC EDGAR download + markdown conversion scripts
├── docs/                    # architecture, guides, claude_desktop_config.json
└── docker-compose.yml
```

---

## Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.12+ | Backend runtime |
| [uv](https://docs.astral.sh/uv/) | latest | Python dependency management |
| Node.js | 20+ LTS | Frontend toolchain |
| pnpm | latest | Frontend package manager |
| [Ollama](https://ollama.com/) | latest | Local LLM inference |
| Docker | latest | Compose-based local stack |

External services: Supabase project (auth + Postgres) and an OpenAI API key (fallback LLM).

---

## Quick Start

### 1. Clone and pull Ollama models (~15 GB)

```bash
git clone <repo>
cd harp
bash backend/scripts/setup_ollama.sh
```

This pulls `phi3`, `mistral`, and `llama3` into Ollama.

### 2. Configure environment

```bash
# Backend
cd backend
cp .env.example .env
```

Fill in `backend/.env`:

```
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
DATABASE_URL=          # direct connection string, not the pooler
OPENAI_API_KEY=        # used as fallback LLM
LANGCHAIN_API_KEY=     # optional, enables LangSmith tracing
ALLOWED_ORIGINS=http://localhost:5173
```

```bash
# Frontend
cd ../frontend
cp .env.example .env
```

Fill in `frontend/.env`:

```
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
```

### 3. Install dependencies and migrate

```bash
cd backend
uv sync
uv run alembic upgrade head

cd ../frontend
pnpm install
```

### 4. Re-embed existing chunks (embedding dimension changed 1536 → 384)

```bash
cd backend
uv run python scripts/reembed_chunks.py
```

### 5. Start with Docker Compose

```bash
# From repo root
docker compose up
```

Or run services individually:

```bash
# Backend
cd backend
uv run uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
pnpm dev
```

Open `http://localhost:5173`.

---

## Ingest SEC Filings

```bash
# Download latest 5 10-K filings for AAPL, MSFT, NVDA, AMZN, GOOGL
uv run data/download.py

# Convert HTML → Markdown
uv run data/convert_to_markdown.py

# Load filing metadata into Supabase
cd backend
uv sync --extra ingest
uv run python -m ingest.load_source_documents

# Chunk and embed (BGE-small, dim=384)
uv run python -m ingest.chunk_and_embed --all

# Force-refresh one filing
uv run python -m ingest.chunk_and_embed --accession 0000000000-00-000000 --force
```

---

## MCP Server (Claude Desktop / Cursor / VS Code)

Copy the provided config to your MCP client:

```bash
# macOS
cp docs/claude_desktop_config.json \
   ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

The MCP server exposes four tools (`document_search`, `document_upload`, `chat_history_lookup`, `document_metadata_lookup`) and three resources (`harp://collections`, `harp://ingestion-status`, `harp://knowledge-base`).

---

## LLM Routing

Queries are routed to one of three local models based on complexity score and retrieval confidence, with automatic OpenAI fallback if the target provider is unhealthy:

| Tier | Provider | When |
|---|---|---|
| SIMPLE | Phi-3 | complexity < 0.3 and confidence ≥ 0.3 |
| MEDIUM | Mistral 7B | complexity 0.3–0.6 or low confidence |
| COMPLEX | Llama 3 8B | complexity ≥ 0.6 or context > 4 000 tokens |
| FALLBACK | OpenAI | provider health check fails |

Clients can override routing by passing a `model_hint` in the request.

---

## Conversation Memory

The `MemoryAgent` persists every user and assistant turn to `conversation_messages`. Every 20 messages it automatically summarizes the conversation using OpenAI and stores the result in `conversation_summaries`. On the next turn the summary plus recent messages are prepended to the retrieval query, giving the agent persistent context across sessions.

---

## Observability

Set `LANGCHAIN_API_KEY` to enable LangSmith tracing. Every `SupervisorAgent` run is wrapped in a `trace_run` context that records name, metadata, and latency. Structured logs via `structlog` are emitted at every major pipeline step (routing decision, retrieval count, memory retrieve/append, citation verification).

---

## Testing

```bash
cd backend

# Unit tests (no external services)
uv run pytest -m "not integration"

# All tests including integration
uv run pytest

# Lint
uv run ruff check .

# Smoke test retrieval pipeline
uv run python scripts/smoke_retrieval.py

# Smoke test full assistant run
uv run python scripts/smoke_assistant.py
```

```bash
cd frontend
pnpm lint
pnpm build
```

---

## Deployment (Railway)

Railway runs two services pointed at the same Supabase project:

- **Frontend** — Vite build served by Caddy (`frontend/Caddyfile`).
- **Backend** — FastAPI + Uvicorn, stateless; all durable state lives in Supabase.

See `docs/guides/railway-deployment.md` for step-by-step setup.

> **Note:** Ollama models run locally or on a separate GPU instance. If you deploy to Railway without a GPU, set `OPENAI_API_KEY` and the router will always fall back to OpenAI.

---

## Environment Variables Reference

### Backend

| Variable | Required | Description |
|---|---|---|
| `SUPABASE_URL` | ✅ | Supabase project URL |
| `SUPABASE_ANON_KEY` | ✅ | Public anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | ✅ | Server-side privileged key |
| `DATABASE_URL` | ✅ | Direct Postgres connection (not pooler) |
| `OPENAI_API_KEY` | ✅ | Fallback LLM + summarization |
| `LANGCHAIN_API_KEY` | ⬜ | Enables LangSmith tracing |
| `ALLOWED_ORIGINS` | ✅ | CORS origin list |
| `RETRIEVAL_TOP_K` | ⬜ | Final fused passages returned (default: 10) |
| `RETRIEVAL_CANDIDATE_K` | ⬜ | Candidates per search path (default: 50) |

### Frontend

| Variable | Required | Description |
|---|---|---|
| `VITE_API_BASE_URL` | ✅ | FastAPI base URL |
| `VITE_SUPABASE_URL` | ✅ | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | ✅ | Public anon key |
