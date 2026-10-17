# Document Intelligence Server

Backend infrastructure for a tagged-document knowledge base: a document-management web UI, an ingestion pipeline (parse → chunk → embed → store), and an **MCP server** exposing the knowledge base as agent-ready tools over Streamable HTTP.

## Architecture

DIS runs as four services orchestrated by Docker Compose: a **React frontend** served by nginx (which also proxies `/api/*` to the backend), a **FastAPI backend** hosting the REST API, the ingestion pipeline, and the MCP server mounted at `/mcp`, **PostgreSQL** for document metadata and parsed text, and **Qdrant** for chunk vectors and filtered semantic search. Browsers talk to the frontend; MCP-compatible agents talk directly to the backend over Streamable HTTP with Bearer authentication.

```mermaid
flowchart TB
    subgraph User
        browser["Browser"]
        agent["MCP Client"]
    end

    subgraph DIS
        frontend["frontend (React)"]
        backend["backend (FastAPI)"]
        db["db (postgres)"]
        qdrant["vector store (qdrant)"]
    end

    browser -->|GET /| frontend
    browser -->|/api/*| backend
    agent -->|"/mcp (Streamable HTTP) Bearer auth"| backend
    frontend -->|/api/* proxy| backend
    backend -->|SQL/asyncpg| db
    backend -->|HTTP| qdrant
```

The repository is organised with this layout:

```
├── .claude/                 Claude Code project config (skills, including the custom SDD skill)
├── .codegraph/              CodeGraph index (code-exploration MCP tool)
├── .github/                 CI workflows
├── backend/                 FastAPI app: REST API + ingestion pipeline + MCP server (see backend/README.md)
├── data/                    Example documents for testing and demos
│   ├── final/               Ready-to-ingest documents in mixed formats
│   ├── raw/                 Source markdown files (one per topic)
│   └── mapping.yaml         Filename → tags mapping
├── docs/                    Part 1 answers
├── frontend/                React SPA for document management (see frontend/README.md)
├── scripts/                 Dev tooling (convert_data.sh, ingest_data.sh)
├── sdd/                     Code specs (managed by the SDD skill)
├── .env.example             Environment template (copy to .env)
├── .mcp.json                MCP client config pointing at the local DIS server
├── CHANGELOG.md             Release history
├── AGENTS.md                Agent instructions (workflow, commands, layout)
├── docker-compose.override.yaml  Dev-only overrides (publishes db/qdrant ports on the host)
├── docker-compose.yaml      Full stack (frontend, backend, db, qdrant)
├── Makefile                 lint / test / build / start / stop / logs
└── README.md                This file
```

## Stack

- **Backend**: Python 3.12, FastAPI (async), SQLModel/asyncpg, uv
- **MCP server**: FastMCP over Streamable HTTP
- **Relational store**: PostgreSQL 17
- **Vector store**: Qdrant (hybrid dense + sparse search)
- **Embeddings**: Qwen3-Embedding-8B via OpenRouter (dense) + FastEmbed BM25 (sparse, local)
- **Parsing / chunking**: markitdown (+ optional VLM OCR), semchunk
- **Frontend**: React 19 + Vite + TypeScript, served by nginx
- **Infra**: Docker Compose (frontend, backend, db, qdrant)

Rationale for each choice is in the two design sections below.

## Knowledge base ingestion pipeline design

The following are rationales and decisions taken for the various parts of the ingestion pipeline.

- **Parsing**. I chose `markitdown` because it's fast and handles many formats out of the box. A similar alternative could have been `docling` or using some low-level libraries (e.g. `pymupdf`) to build a custom parser, other approaches could have relied more heavily or totally on VLMs. In the first iteration (v0.1.0) I opted for the default out-of-the-box parsing, in a later refinement (v0.1.1) I added OCR for in-doc images and scanned docs using a VLM.
- **Chunking**. Here I used `semchunk`, which is a standard chunker that does a bit more effort to split text semantically (end of paragraphs, sections etc, heuristically) and thus is slightly more performant compared to other out-of-the-box chunkers (see [here](https://github.com/isaacus-dev/semchunk#benchmarks-)). Here there are other more refined approaches that could have been taken: a simple idea is using a LLM pass on the parsed doc to refine the markdown section structure and then building a custom chunker to split on markdown sections and dividers, or one could think about other approaches that use LLMs to improve chunk quality (a standard example is Contextual Retrieval which basically prepends doc/chunk summaries to raw chunk text)
- **Embedding**. I used `qwen3-embedding-8B` as an embedding model (most used on OpenRouter). It offers a good balance of low cost, good performances and modern features, such as Matryoshka embeddings to reduce the embedding dimension at will, and asymmetric search for document vs query.
- **Vector store**. The choice here was between pgvector to just add an extension to the db service and a pure vector store (Qdrant). The latter was chosen because of native support of more advanced functionalities, namely hybrid search. I used tag and document ids filters with hybrid search (local BM25 for sparse vectors) and RRF for combining the score (fast and deterministic). Reranking was not considered here (would add latency, hardware considerations).
- **Deduplication**. On upload we detect a duplicate by checking the hash of the raw bytes of the document. This allows us to perform the deduplication check before any actual ingestion operation. An alternative could have been to deduplicate on parsed text, but I chose not to go this way since it's not a given that we choose a deterministic parser or that parsing is cost-free.
- **Ingestion endpoint**. The ingestion process is split in two phases: preparation (where we check for duplicates and assign the doc id) and finalisation, where we execute the actual parse->chunk->embed->load pipeline. With this approach, the ingestion endpoint can execute the preparation phase, spawn a background process and return the doc id. This way the response is fast and non-blocking, and the frontend can poll with doc id to get status updates.

The end-to-end ingestion process looks like this:


```mermaid
sequenceDiagram
    participant U as User/Client
    participant API as POST /api/documents/upload
    participant I as IngestionService
    participant P as Parser
    participant R as DocumentRepo
    participant V as VectorStore

    U->>API: multipart (file + tags)
    API->>I: prepare(content, filename, tags)
    I->>I: SHA-256(raw bytes) → content_hash
    I->>R: get_by_hash(hash)
    alt hash exists (dedup)
        R-->>I: existing Document
        I-->>API: raise DuplicateDocumentError
        API-->>U: 409 Conflict (duplicate)
    else new document
        I->>P: parse(content)
        P-->>I: markdown text
        I->>R: create(status=processing)
        R-->>I: Document
        I-->>API: Document
        API-->>U: 202 Accepted (processing)
        API->>I: background: finalize(id)
        I->>P: chunk(text)
        I->>I: embed(chunks)
        I->>V: upsert(records, vectors)
        I->>R: update_status(ready)
        alt failure
            I->>R: update_status(failed, error)
        end
    end
```

Other notes:

- The choices taken were somewhat "standard", with the addition of some sensible enhancements. This was done in spirit with the assignment expected execution time, but I also want to consider that these choices should be guided by the particular IR problem at hand: dimension of KB, complexity of documents, presence and importance of images, update strategy. In this my idea was going for a stack that is general enough to be reliable in a standard RAG scenario, but the real upgrade would come to task-aware specialization.
- For example something that we're seeing more of in these days is pairing a classic vector store with some kind of virtual filesystem where the agent can research documents "naturally" just by reading index files and the actual files (llm wiki, agentic file search). This is interesting but seems to lose value on very big knowledge bases. Another alternative that is very powerful for some narrow/specific domains are graph DBs.

## MCP server design

Four tools are registered: `list_documents`, `list_tags`, `search`, `get_document`. The assignment's `search_by_tag` / `search_by_document` are deliberately folded into `search`'s `tags` / `document_ids` filters rather than kept as separate tools, to avoid tool-choice ambiguity for the calling agent. `get_document` is an addition beyond the proposed five: search returns isolated chunks, and once the agent has identified the right document it needs a way to read more of it (neighboring chunks around a hit for more context, or the full text for a deep dive).

NB: I don't think there is a best general solution to having one broader tool vs more specific ones, and as for the ingestion pipeline the choice should be guided by the specifics of the knowledge base at hand, and possibly some proper evaluations on how the agent is performing with different setups of MCP tools. With that said, I personally would start simple with a single search tool, and evaluate the necessity of another configuration based on performance.

The registered tools and their parameters:

- **`list_documents`**: returns document metadata (filename, ID, tags, status, chunk count, token count, upload date). Parameters: `offset` (int ≥ 0, default 0), `limit` (int 1–500, default 100), `tag` (optional string, filters to documents carrying that exact tag).
- **`list_tags`**: returns all unique tags currently assigned to at least one document, sorted alphabetically. No parameters.
- **`search`**: hybrid semantic + keyword search over chunks. Parameters: `query` (non-empty string), `top_k` (int 1–50, default 5), `tags` (optional list, OR semantics), `document_ids` (optional list of UUIDs; combined with `tags` both filters must match).
- **`get_document`**: reads a document's content by ID. Parameters: `document_id` (UUID), `chunks` (optional list of chunk indices, as reported in `search` hits). Without `chunks` it returns the full parsed text; documents above a configured token limit (`MAX_DOCUMENT_READ_TOKENS`, default 20000) are refused with a hint to request specific `chunks` or use `search` instead.

A few notes on the agent interface:

- **Self-describing constraints.** Parameter bounds are declared as Pydantic constraints, so they appear in the JSON schema the agent sees and are enforced server-side. Defaults are chosen so a bare `search(query=...)` call just works.
- **Cross-referenced descriptions.** The tool descriptions link to each other to teach the workflow: `list_tags` and `list_documents` say "use this to discover valid filter values before calling `search`", and `search` says it is the primary retrieval tool and points back at the two discovery tools.
- **LLM-readable output.** Tools return compact formatted text rather than raw JSON in order to be more token-efficient. Each search hit carries its source document, tags, chunk index, and score (fused RRF rank)
- **Clean error surface.** Domain errors (bad document ID, embedding provider failure) are translated into short `ToolError` messages the agent can act on; anything unexpected propagates as a server error instead.

Note: Another addition I didn't include but personally consider interesting, is pairing the MCP server with a skill that thoroughly describes how to use the tools. This way one could keep tool descriptions lighter, and also add a more precise workflow description, examples and so on.

## Deploy

Deployment is completely local for now.

Only Docker (Engine 24+ with the Compose v2 plugin, i.e. `docker compose`) and an OpenRouter/OpenAI API key are required to run the application locally. For development purposes, please make sure to have `uv`, `prek` and `bun` installed (plus curl for the example data ingestion script).

Clone the project, then use `cp .env.example .env` to copy the example environment file. Set OPENROUTER_API_KEY (you can also use an OpenAI key, see `.env.example` for specifics).

After this, run:

```bash
make build
make start
```

Then open the web UI in your browser:

- **Frontend (web UI): http://localhost:3000**
- REST API Swagger: http://localhost:8000/docs (or /redoc)
- Qdrant dashboard: http://localhost:6333/dashboard

Optionally load example data after starting the stack:
```bash
bash scripts/ingest_data.sh   # POST data/final/* to the running API
```

Note: one example document (`architecture-overview.pdf`) is a scanned, image-only PDF and needs `USE_VLM=true` in `.env` to be parsed; with the default settings the script reports it as skipped and ingests the other seven.

To upgrade this stack to a remote deployment exposed publicly, these would be the additions/modifications to take into consideration:

- **TLS + reverse proxy**: the frontend's nginx already proxies `/api/*`, but it does no TLS and the backend's port 8000 (where MCP clients connect) bypasses it entirely. Promote that role to a proper edge proxy (Caddy/Traefik/nginx) as the only public entrypoint: terminate HTTPS there, route `/`, `/api` and `/mcp`, and stop publishing the backend port.
- **Auth**: the MCP endpoint has a basic Bearer token auth, while the REST API is currently unauthenticated: it would need an auth layer, or to stay reachable only from a private network/VPN. Both data stores must also be secured (currently their ports are exposed to the local host for development via `docker-compose.override.yaml`).
- **Secrets**: real secrets injected via some CI/CD system (e.g. GitHub Actions)
- **Storage**: It would probably make sense to use managed instances of Postgres/Qdrant in a real production setting, or at least manage volumes backup properly.
- **Deployment**: the simplest viable flow is SSH to the host and `git pull && make build && make start`; a step up is CI building the images and a webhook/action triggering the redeploy.

## How to connect an MCP client

Run the stack locally, then point any MCP-compatible client at:

```
URL:    http://localhost:8000/mcp
Header: Authorization: Bearer <MCP_API_KEY>   # dev default: dev-mcp-key-change-me
```

Example `.mcp.json` for Claude:

```json
{
  "mcpServers": {
    "dis-knowledge-base": {
      "type": "http",
      "url": "http://localhost:8000/mcp",
      "headers": {
        "Authorization": "Bearer dev-mcp-key-change-me"
      },
      "lifecycle": "lazy",
      "directTools": true
    }
  }
}

```

Note: the endpoint canonically lives at `/mcp/` — a bare `/mcp` gets a 307 redirect (Starlette mount behavior) that standard MCP clients follow transparently.

MCP clients connect to `/mcp` and the SDK handles the protocol. Auth is enforced on the JSON-RPC endpoint: a request without the token gets `401`. See [MCP server design](#mcp-server-design) for the registered tools and their rationale.

## Backlog

No active backlog. See [CHANGELOG.md](CHANGELOG.md) for release history.


## Known limitations & future improvements

Ingestion & retrieval:

- Dedup is byte-exact (SHA-256 of the upload): the same document re-exported with different bytes is not detected, and re-upload returns 409 rather than updating tags.
- A failed ingestion can only be retried by deleting and re-uploading; there is no automatic retry.
- Parsing runs inside the upload request (before the 202), so very large or VLM-parsed documents make the upload call slow.
- No reranking stage and no retrieval evaluation harness (golden question set, recall@k) to measure search quality objectively.
- Original files are not retained — only the parsed markdown is stored, so re-chunking with different parameters requires re-upload.
- MCP tools return text only (no structured content), and the server exposes no MCP resources or prompts.

Backend & architecture:

- No schema migrations (tables are created from SQLModel metadata on startup) — fine for a fresh install, not for evolving a production schema.
- The REST API is unauthenticated and its port is published on the host (Postgres/Qdrant ports are published only in dev, via `docker-compose.override.yaml`): acceptable for local development, to be locked down for any real deployment.
- MCP auth is a single static Bearer token — no per-client keys, scopes, or rotation.
- Background ingestion runs in-process: tasks die with the server (a startup sweep marks stuck documents as failed) — a real queue (e.g. arq/Celery) would make this durable.
- Single backend instance assumed; no rate limiting or upload size cap.

## Part 1 — Written answers

See [docs/part1_answers.md](docs/part1_answers.md).
