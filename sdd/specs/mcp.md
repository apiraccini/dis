# MCP Tools

## MCP Server Access

- **Requirement: MCP server is accessible at /mcp** — A separate FastMCP instance SHALL
  be mounted at `/mcp` on the main FastAPI app, serving Streamable HTTP with the
  existing static Bearer-token auth
  - Scenario: GET on /mcp returns 307 redirect — GIVEN no Bearer token, WHEN an
    MCP client connects via GET /mcp, THEN the response is 307 redirect to /mcp/
  - Scenario: POST on /mcp/ with valid token succeeds — GIVEN a valid Bearer token,
    WHEN the client sends a JSON-RPC request to POST /mcp/, THEN the request is
    processed (e.g. `ping` → `pong`)

## Tool: list_documents

- **Requirement: list_documents tool** — `list_documents` SHALL return paginated
  documents (id, filename, tags, status, chunk_count, created_at) without parsed_text
  - Input: `offset` (int, default 0), `limit` (int, default 100, max 500),
    `tag` (optional str)
  - Output: list of document summaries + `total` count
  - Scenario: tag filter — GIVEN documents with tags, WHEN `list_documents` is called
    with `tag=compliance`, THEN only documents whose tags contain `compliance` are
    returned
  - Scenario: pagination — GIVEN 150 documents, WHEN `list_documents` is called with
    `offset=0, limit=100`, THEN 100 documents are returned and `total=150`

## Tool: list_tags

- **Requirement: list_tags tool** — `list_tags` SHALL return all unique tags sorted
  alphabetically
  - Input: none
  - Output: `{tags: ["audit", "compliance", ...]}`
  - Scenario: no documents — GIVEN an empty database, WHEN list_tags is called, THEN
    `{tags: []}` is returned

## Tool: search

- **Requirement: search tool** — `search` SHALL semantically search all chunks using
  query-time embeddings (`input_type=search_query`) and return top-k hits ranked by
  descending similarity
  - Input: `query` (str, required), `top_k` (int, default 5, max 50),
    `tags` (optional list[str], OR semantics), `document_ids` (optional list[str],
    UUID membership)
  - Output: list of `SearchHit` — each with `document_id`, `document_name`, `tags`,
    `chunk_index`, `text`, `score` (float, 0..1)
  - Scenario: unfiltered search — GIVEN chunks with varied content, WHEN `search` is
    called with a query and no filters, THEN hits from all documents are returned
  - Scenario: tag-filtered search — WHEN `search` is called with `tags=["compliance"]`,
    THEN only chunks whose document carries the `compliance` tag are returned
  - Scenario: document-filtered search — WHEN `search` is called with a specific
    `document_ids`, THEN only chunks from those documents are returned
  - Scenario: combined filters — WHEN both `tags` and `document_ids` are specified,
    THEN only chunks matching both filters are returned (intersection)

## Tool: search_by_tag

- **Requirement: search_by_tag tool** — `search_by_tag` SHALL be a convenience wrapper
  around `search` that passes `tags` directly
  - Input: `query` (str), `tags` (required list[str], OR semantics), `top_k` (int,
    default 5, max 50)
  - Output: same as `search`
  - Scenario: single tag — GIVEN `tags=["compliance"]`, WHEN `search_by_tag` is called,
    THEN it behaves identically to `search` with `tags=["compliance"]`

## Tool: search_by_document

- **Requirement: search_by_document tool** — `search_by_document` SHALL be a convenience
  wrapper around `search` that passes `document_ids` directly
  - Input: `query` (str), `document_ids` (required list[str], UUID membership),
    `top_k` (int, default 5, max 50)
  - Output: same as `search`
  - Scenario: single document — GIVEN a document UUID, WHEN `search_by_document` is
    called, THEN only chunks from that document are returned

## Dependency Injection

- **Requirement: Tools use FastMCP Depends() for DI** — MCP tools SHALL receive the
  Adapters singleton via `Depends(get_adapters)` and the document repository via
  `Depends(get_document_repo)`, following fastmcp's recommended dependency injection
  pattern

## Embedding

- **Requirement: Query embedding uses search_query input_type** — MCP search tools SHALL
  use an embedder configured with `input_type=search_query` (asymmetric retrieval),
  separate from the index-time embedder built with `input_type=search_document`

## Removed Tools

- **Requirement: ping tool replaced** — The `ping` smoke tool SHALL be removed once
  the five knowledge-base tools are registered
  - Scenario: client calls ping — GIVEN a client, WHEN `ping` is called, THEN a
    `ToolNotFound` error is returned
