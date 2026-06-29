# Design: MCP Knowledge-Base Tools

## Intent

Expose the document knowledge base as agent-ready MCP tools over Streamable HTTP
at `/mcp`. An AI agent discovers documents, lists tags, and semantically searches
the vector store — enabling retrieval-augmented questioning without going through
the REST API.

## Scope

**In scope:**
- Five MCP tools: `list_documents`, `list_tags`, `search`, `search_by_tag`,
  `search_by_document`
- `search` accepts optional `tags` and `document_ids` filter params (broader queries)
- `search_by_tag` / `search_by_document` are convenience wrappers (redundancy not a problem)
- Pagination on `list_documents` (offset/limit, sensible defaults)
- Query-time embedding uses `input_type=search_query` (asymmetric retrieval)
- Results expose chunk text + similarity score + source metadata
- Remove the `ping` smoke tool after real tools land
- Snake_case tool names

**Out of scope:**
- `get_document` MCP tool (agent gets full text via REST API if needed)
- Document upload/delete via MCP (handled by REST API)
- RAG-specific tools (prompt templates, context assembly)
- SSE transport (already Streamable HTTP)
- MCP usage skill for agents (added to backlog)
- Auth beyond existing static Bearer token

## Approach

- Decision: FastMCP `Depends()` for dependency injection — `CurrentRequest()` + `request.app.state` is
  indirect and couples to HTTP transport. Instead, store a module-level reference to the
  `Adapters` singleton and inject it via `Depends(get_adapters)`. FastMCP's `Depends()` is
  transport-agnostic (works with STDIO, SSE, Streamable HTTP) and follows the recommended
  pattern. The same module-level reference is also set on `app.state` for the REST API
  endpoints (which already depend on it via FastAPI `Depends`).
- Decision: query-time embedder — the factory builds a second `OpenRouterEmbedder` instance
  with `input_type=search_query` held as `adapters.query_embedder`. The existing
  `adapters.embedder` stays `search_document` for index-time use. No protocol changes needed.
- Decision: DB session per tool call — each MCP tool that needs document data creates a
  fresh `async_session` via `Depends(get_document_repo)`, matching the REST API pattern.
  The `get_document_repo` dependency opens a session → creates `SqlModelDocumentRepository`
  → yields it → closes on return.
- Decision: snake_case tool names matching Python function names (agents see the function
  name as the tool name in MCP protocol).
- Decision: `search`, `search_by_tag`, `search_by_document` all embed the query string
  using `adapters.query_embedder`, then call `adapters.vectors.search()` with the
  appropriate filters. `search_by_tag` passes `tags=[...]`, `search_by_document` passes
  `document_ids=[...]`, and `search` passes both if provided.
- Decision: `list_documents` returns documents without `parsed_text` (same as the REST
  list endpoint — too large). `list_tags` returns all unique sorted tags.
- Decision: `ping` tool removed once the five real tools are registered.

## Affected Domains

- NEW: `sdd/specs/mcp.md` — MCP tool requirements
- `sdd/specs/ingestion.md` — no delta (embedding flow unchanged; query embedder is a
  factory concern, not a pipeline concern)
- `sdd/specs/vectors.md` — no delta (search/filter pushdown already spec'd)
- `sdd/specs/documents.md` — no delta (model already supports everything needed)
