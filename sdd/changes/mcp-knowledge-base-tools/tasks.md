# Tasks: MCP Knowledge-Base Tools

## Setup: module-level adapters singleton + query embedder

- [x] 1.1 Add `query_embedder: Embedder` field to `Adapters` dataclass in `services/factory.py`
- [x] 1.2 Build the query embedder in `build_adapters()` using `embedding_input_type_query`
      from settings
- [x] 1.3 Add module-level `_adapters: Adapters | None = None` + `set_adapters()` / `get_adapters()`
      in a new file `services/di.py`
- [x] 1.4 Call `set_adapters(adapters)` in `main.py` lifespan alongside `app.state.adapters = adapters`
- [x] 1.5 Create `get_document_repo()` async context manager dependency for MCP tools
      (opens `async_session`, creates `SqlModelDocumentRepository`, yields, closes)

## MCP tools implementation

- [x] 2.1 Write `list_documents` tool — uses `Depends(get_document_repo)`, calls
      `repo.list_documents(offset, limit, tag)`, returns paginated summaries
- [x] 2.2 Write `list_tags` tool — uses `Depends(get_document_repo)`, queries up
      to 10K docs, aggregates unique tags, returns sorted
- [x] 2.3 Write `search` tool — uses `Depends(get_adapters)`,
      `adapters.query_embedder.embed([query])` → vector → `adapters.vectors.search()`
      with optional tags/document_ids, returns list of SearchHit dicts
- [x] 2.4 Write `search_by_tag` tool — delegates to the same logic as `search` with
      mandatory `tags` param
- [x] 2.5 Write `search_by_document` tool — delegates to the same logic as `search`
      with mandatory `document_ids` param
- [x] 2.6 Remove the `ping` tool from `mcp_server.py`
- [x] 2.7 Remove `ping` from `__all__` / any references
- [x] 2.8 Ensure all five tools are registered on the `mcp` instance before `mcp.http_app()`

## Testing

- [x] 3.1 Write unit tests for each MCP tool using the in-memory fakes (
      `InMemoryDocumentRepository` + `InMemoryVectorStore` + a fake embedder)
      — test: list_documents pagination, list_tags empty/populated, search with
      and without filters, search_by_tag, search_by_document, tool-not-found
      for removed ping
- [x] 3.2 Run existing test suite to confirm no regressions (86→101 tests)

## Verification

- [x] 4.1 `make lint` passing (ruff + ty)
- [x] 4.2 `make test` all 101 tests passing
- [x] 4.3 (optional) `make start` + connect pi to the live MCP endpoint and run a
      search: `mcp({ search: "list_documents" })` then `mcp({ tool: "list_documents" })`
