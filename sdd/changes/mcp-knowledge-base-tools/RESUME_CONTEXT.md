# Resume Context: MCP Knowledge-Base Tools

## Session Boundary

SDD Phase 2 (Plan) is complete. The next session starts SDD Phase 3 (Execute).
Load the execute reference from:
`.agents/skills/spec-driven-development/references/execute.md`

## Change Folder

`sdd/changes/mcp-knowledge-base-tools/`

| Artifact | Path |
|----------|------|
| Design | `design.md` |
| Delta spec | `specs/mcp.md` |
| Tasks | `tasks.md` |

## Key Decisions

1. **DI pattern:** FastMCP `Depends()` with module-level adapter singleton
   (NOT `CurrentRequest()` + `request.app.state`). Create `services/di.py` (or `core/mcp_deps.py`)
   with `set_adapters()` / `get_adapters()`. Also add `get_document_repo()` that opens a session.

2. **Query embedder:** A second `OpenRouterEmbedder` with `input_type=search_query` stored as
   `adapters.query_embedder`. The existing `adapters.embedder` stays at `search_document`.

3. **Five tools + removed ping:** `list_documents`, `list_tags`, `search`, `search_by_tag`,
   `search_by_document`. Remove the `@mcp.tool` decorator for `ping`.

4. **`search` has optional `tags`/`document_ids` params.** `search_by_tag` and `search_by_document`
   are convenience wrappers passing mandatory filters.

5. **All results include chunk text + score + source metadata.** No `parsed_text` in list.

## Files to Modify

| File | Changes |
|------|---------|
| `backend/src/services/factory.py` | Add `query_embedder` to `Adapters` dataclass + build in `build_adapters()` |
| `backend/src/main.py` | Call `set_adapters(adapters)` in lifespan |
| `backend/src/mcp_server.py` | Register 5 tools, remove ping. Import deps from new file |
| `backend/src/core/mcp_deps.py` (NEW) | Module-level `_adapters` + `set_adapters()`/`get_adapters()` + `get_document_repo()` Depends |
| `backend/tests/test_mcp_tools.py` (NEW) | Unit tests using in-memory fakes |

## Prerequisites Check

- `make lint` ✅ passes
- `make test` ✅ 86/86 passing
- MCP server skeleton works ✅ (`/mcp` mounted, auth, ping responds)
- Vector store has `search()` with filter pushdown ✅
- REST API works ✅
- Qdrant collection auto-provisions ✅
