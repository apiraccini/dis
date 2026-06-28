# Document Intelligence Server

Backend infrastructure for a tagged-document knowledge base: a document-management web UI, an ingestion pipeline (parse → chunk → embed → store), and an **MCP server** exposing the knowledge base as agent-ready tools over Streamable HTTP.

> **State: scaffold only.** The harness (lint, tests, Docker, CI, MCP endpoint wiring, auth) is green and verified. There is **no business code yet** — no data models, no REST endpoints beyond `/health`, no ingestion pipeline, and only a `ping` smoke-test MCP tool. The backlog below is the map of what needs building. See `REQUEST.md` for the original assignment.

## Architecture

Four services (see `docker-compose.yaml`):

- **db** — PostgreSQL 17: raw document metadata (documents, tags, chunks).
- **qdrant** — vector store: chunk embeddings + payload (document id/name, tags) for filtered semantic search.
- **backend** — one FastAPI app serving:
  - REST API for document management + ingestion (`/api/...`)
  - MCP server mounted at `/mcp` (FastMCP, Streamable HTTP, static Bearer-token auth)
- **frontend** — React SPA (nginx-served, proxies `/api` to the backend).

```
┌──────────┐     /api      ┌──────────┐      SQL       ┌────────┐
│ frontend │ ────────────▶ │ backend  │ ─────────────▶  │   db   │  (Postgres: metadata)
│  (React) │ ◀───────────  │ (FastAPI)│                 └────────┘
└──────────┘               │   + MCP  │      gRPC/HTTP ┌────────┐
                           │  at /mcp │ ─────────────▶  │ qdrant │  (vectors + payload)
                           └──────────┘                 └────────┘
```

## Stack choices & rationale

| Area | Choice | Why |
|---|---|---|
| Vector store | **Qdrant** | Dedicated, production-like vector DB. Payload filtering lets `search_by_tag` / `search_by_document` push the filter into the vector query (single round-trip, no post-filtering). Postgres+pgvector was considered but a dedicated store matches the "production-like" brief and keeps vector concerns out of the relational schema. |
| Relational store | **PostgreSQL 17** via SQLModel/asyncpg | Document metadata (filename, tags, upload date, chunk count) is relational; Postgres is standard, reliable, and already in the stack. |
| Embedding model | **OpenAI** (model TBD) | An OpenAI key is provided per the brief. The exact model (`text-embedding-3-small`/`-large`) is decided in the first SDD session once the vector dimension and cost/quality trade-off are pinned; `EMBEDDING_MODEL`/`EMBEDDING_DIMENSIONS` are empty in `.env.example` until then. |
| Chunking | **semchunk** (semantic) | Semantic chunking splits on natural topic boundaries, preserving meaning per chunk — better retrieval quality than fixed-size char splits. Wrapped behind a `Chunker` Protocol so the strategy is swappable. |
| Parsing | **liteparse** | Lightweight multi-format parser (PDF + plain text minimum). Wrapped behind a `Parser` Protocol. |
| MCP transport | **Streamable HTTP** | Required by the brief. Served via FastMCP's `http_app(stateless_http=True, json_response=True)` mounted into the FastAPI app at `/mcp`. Stateless mode means no server-side session affinity is needed to scale horizontally. |
| MCP SDK | **`fastmcp`** (standalone, PrefectHQ/fastmcp) | Cleaner mounting API than the `mcp` SDK's built-in server: `http_app()` returns an ASGI app with a `.lifespan` attribute, composed into FastAPI via `combine_lifespans`. |

### Key decisions
- **MCP folded into the FastAPI app** (`src/mcp_server.py` + `src/main.py` mount): one process, shared settings, one deploy. The mounted FastMCP ASGI sub-app gets its lifespan composed into FastAPI via `combine_lifespans`.
- **No Alembic**: schema via `SQLModel.metadata.create_all` on startup (documented limitation — switch to Alembic if migrations become a concern).
- **Auth trimmed**: no JWT/login. The MCP endpoint is the only network-exposed sensitive surface (returns private KB contents to agents); it is gated by a static Bearer token via FastMCP's `StaticTokenVerifier`. The REST API is unauthenticated — internal to the compose network; add auth before exposing it publicly.
- **Ingestion stages are Protocols** (`services/protocols.py`): `Parser`, `Chunker`, `Embedder`. Each concrete impl lands behind its interface, so parser/chunker/embedder can be improved independently.

### MCP tool design rationale
The five required tools (`list_documents`, `list_tags`, `search`, `search_by_tag`, `search_by_document`) are **not yet implemented** — they are the first SDD implementation session (see Backlog). Their input schemas, output shapes, and descriptions will be designed from the agent's perspective (what an LLM sees to decide when/how to call each tool) and documented here when they land. A single `ping` tool is registered now as a smoke test of the MCP wiring and auth.

## Quick start

```bash
cp .env.example .env
make build
make start
```

- REST API: http://localhost:8000 (health at `/health`)
- MCP endpoint: http://localhost:8000/mcp (Bearer token = `MCP_API_KEY`)
- Frontend: http://localhost:3000

Dev without Docker:
```bash
cd backend && uv sync --dev && uv run uvicorn src.main:app --reload   # needs db + qdrant reachable
cd frontend && bun install && bun run dev
```

## Connecting an MCP client

Point any MCP-compatible client (Claude Desktop, MCP Inspector, a custom agent) at:

```
URL:    http://localhost:8000/mcp
Header: Authorization: Bearer <MCP_API_KEY>   # dev default: dev-mcp-key-change-me
```

MCP clients connect to `/mcp` and the SDK handles the protocol; raw HTTP probes must POST to `/mcp/` (trailing slash) — a GET on `/mcp` returns a 307 redirect. Auth is enforced on the JSON-RPC endpoint: a request without the token gets `401`. Currently only `ping` is exposed; the five knowledge-base tools arrive with the backlog.

## Backlog

### Backend
- [ ] Data models + repositories (Document, Tag, Chunk; SQLModel tables + Protocol-based repos)
- [ ] Document management REST API (upload, list, delete; schemas + endpoints; re-upload does not duplicate)
- [ ] Ingestion pipeline (liteparse parser, semchunk chunker, embedder impl, Qdrant storage, dedup)
- [ ] MCP tools (`list_documents`, `list_tags`, `search`, `search_by_tag`, `search_by_document`) + tool-design rationale

### Frontend
- [ ] Document management UI (upload + tag, list, delete)

## Known limitations (scaffold state)
- **No business code**: only `/health` and the MCP `ping` tool exist. Everything in the Backlog is unimplemented.
- **No Alembic**: tables auto-created from `SQLModel.metadata.create_all`; no migration history. Fine at this scale; revisit if schema evolves.
- **REST API unauthenticated**: internal to the compose network only. Add auth before any public exposure.
- **No live deployment / demo video**: out of scope for the scaffold; `docker compose` is the run method. Deployment and the demo video are deferred to a later session.
- **Embedding model undecided**: `EMBEDDING_MODEL`/`EMBEDDING_DIMENSIONS` empty in `.env.example`; set during the ingestion-pipeline SDD session.

## Repo layout
```
backend/    FastAPI app (REST + ingestion) + MCP server (see backend/README.md)
frontend/   React SPA (see frontend/README.md)
sdd/        specs and change folders
REQUEST.md  original assignment
```

## Workflow
See `AGENTS.md`. Spec-Driven Development drives implementation; specs live in `sdd/specs/`.
