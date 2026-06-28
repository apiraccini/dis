# Document Intelligence Server

Backend infrastructure for a tagged-document knowledge base: a document-management web UI, an ingestion pipeline (parse → chunk → embed → store), and an **MCP server** exposing the knowledge base as agent-ready tools over Streamable HTTP.

> **State: ingestion core done.** The harness (lint, tests, Docker, CI, MCP endpoint wiring, auth) is green, the data models + repositories are in, and the ingestion pipeline now runs end-to-end with real adapters (markitdown → semchunk → Qwen3-embedding-8b via OpenRouter → Qdrant), verified by a live integration smoke. Not yet exposed: the document-management REST API, the five MCP knowledge-base tools, and the frontend UI — those are the next backlog items.

## Architecture

Four services (see `docker-compose.yaml`):

- **db** — PostgreSQL 17: document metadata (documents, tags) + parsed full text.
- **qdrant** — vector store: chunk text + embeddings + payload (document id/name, tags) for filtered semantic search. No chunk rows in Postgres.
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
| Embedding model | **Qwen3-Embedding-8B** via OpenRouter | 8B-param multilingual model (100+ languages), 32k context, native dim up to 4096 with Matryoshka truncation. Served through OpenRouter's OpenAI-compatible embeddings endpoint (`base_url=https://openrouter.ai/api/v1`) using the existing `openai` SDK — no new dependency. Truncated to **1536 dims** (strong retrieval at ~40% of 4096 storage cost). Supports asymmetric retrieval via `input_type` (`search_document` at index time, `search_query` at query time). Chosen over OpenAI `text-embedding-3-small` to exercise a non-OpenAI provider through a compatible API and for stronger multilingual coverage relevant to an enterprise KB. |
| Chunking | **semchunk** (semantic, ~1024 tokens, no overlap) | Semantic chunking splits on natural topic boundaries, preserving meaning per chunk — better retrieval quality than fixed-size char splits. ~1024-token chunks balance context-per-chunk against retrieval granularity; no overlap because semantic boundaries already preserve meaning across splits (keeps chunk count clean and dedup simple). Wrapped behind a `Chunker` Protocol so the strategy is swappable; size/overlap configurable in `config.py`. |
| Parsing | **markitdown** | Microsoft's Markdown-first converter (PDF + Office + plain text). Pure-Python deps (`pdfminer.six`, `pdfplumber`, `python-docx/pptx`, `openpyxl`) keep the Docker image small — no LibreOffice/ImageMagick/Tesseract system packages. Markdown output (headings, tables, lists, links) preserves structure that improves retrieval quality over flat text. Wrapped behind a `Parser` Protocol. Scanned-PDF OCR is a deferred refinement (candidate: `markitdown-ocr` LLM-vision plugin via the OpenRouter key). |
| MCP transport | **Streamable HTTP** | Required by the brief. Served via FastMCP's `http_app(stateless_http=True, json_response=True)` mounted into the FastAPI app at `/mcp`. Stateless mode means no server-side session affinity is needed to scale horizontally. |
| MCP SDK | **`fastmcp`** (standalone, PrefectHQ/fastmcp) | Cleaner mounting API than the `mcp` SDK's built-in server: `http_app()` returns an ASGI app with a `.lifespan` attribute, composed into FastAPI via `combine_lifespans`. |

### Key decisions
- **MCP folded into the FastAPI app** (`src/mcp_server.py` + `src/main.py` mount): one process, shared settings, one deploy. The mounted FastMCP ASGI sub-app gets its lifespan composed into FastAPI via `combine_lifespans`.
- **No Alembic**: schema via `SQLModel.metadata.create_all` on startup (documented limitation — switch to Alembic if migrations become a concern).
- **Auth trimmed**: no JWT/login. The MCP endpoint is the only network-exposed sensitive surface (returns private KB contents to agents); it is gated by a static Bearer token via FastMCP's `StaticTokenVerifier`. The REST API is unauthenticated — internal to the compose network; add auth before exposing it publicly.
- **Ingestion stages are Protocols** (`services/protocols.py`): `Parser`, `Chunker`, `Embedder`. Each concrete impl (`markitdown` parser, `semchunk` chunker, OpenRouter embedder, Qdrant store) lands behind its interface, so parser/chunker/embedder can be improved independently.

### MCP tool design rationale
The five required tools (`list_documents`, `list_tags`, `search`, `search_by_tag`, `search_by_document`) are **not yet implemented** — they are the next SDD implementation session (see Backlog), now that ingestion + search are functional. Their input schemas, output shapes, and descriptions will be designed from the agent's perspective (what an LLM sees to decide when/how to call each tool) and documented here when they land. A single `ping` tool is registered now as a smoke test of the MCP wiring and auth.

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
- [x] Data models + repositories (Document [parsed content + content-hash dedup], Tag, DocumentTag many-to-many link; SQLModel tables + Protocol-based repos; no Chunk table — chunks live in Qdrant)  _(done with a revision: tags stored as a Postgres `text[]` column on Document instead of a Tag/DocumentTag link — see `sdd/specs/documents.md`)_
- [x] Ingestion pipeline (markitdown parser, semchunk chunker, OpenRouter embedder; standalone services storing chunk text + embedding + payload in Qdrant, parsed content + metadata in Postgres)  _(done: `IngestionService` two-phase prepare/finalize + `VectorStore` Protocol; concrete adapters — `MarkItDownParser`, `SemchunkChunker`, `OpenRouterEmbedder`, `QdrantVectorStore` — implemented behind their Protocols, unit-tested, and verified end-to-end via a live compose smoke; Qdrant collection auto-provisioned on startup with cosine distance + payload indexes on `document_id`/`tags`; two pre-existing bugs fixed during integration — `db.py` session type and `Document` timestamp columns — see `sdd/specs/ingestion.md` + `vectors.md`)_
- [ ] Document management REST API (upload → triggers ingestion, list, delete → cascades to Qdrant; dedup via content hash)
- [ ] MCP tools (`list_documents`, `list_tags`, `search`, `search_by_tag`, `search_by_document`) + tool-design rationale

### Frontend
- [ ] Document management UI (upload + tag, list, delete)

## Known limitations (current state)
- **No exposed API surface yet**: only `/health` and the MCP `ping` tool are reachable. The document-management REST API and the five MCP knowledge-base tools are the next backlog items — the ingestion pipeline and search are functional but not yet wired to endpoints.
- **No Alembic**: tables auto-created from `SQLModel.metadata.create_all`; no migration history. Fine at this scale; revisit if schema evolves.
- **REST API unauthenticated**: internal to the compose network only. Add auth before any public exposure.
- **No live deployment / demo video**: out of scope for the scaffold; `docker compose` is the run method. Deployment and the demo video are deferred to a later session.
- **Scanned-PDF OCR not supported**: markitdown parses born-digital PDFs and Office docs; scanned-PDF OCR is a deferred refinement (candidate: the `markitdown-ocr` LLM-vision plugin via the OpenRouter key).
- **Embedding model**: `qwen/qwen3-embedding-8b` via OpenRouter, 1536 dims (Matryoshka). Only `OPENROUTER_API_KEY` is secret; model/dimensions/chunk params live in `config.py` with defaults.

## Repo layout
```
backend/    FastAPI app (REST + ingestion) + MCP server (see backend/README.md)
frontend/   React SPA (see frontend/README.md)
sdd/        specs and change folders
```

## Workflow
See `AGENTS.md`. Spec-Driven Development drives implementation; specs live in `sdd/specs/`.
