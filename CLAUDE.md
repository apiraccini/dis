# Document Intelligence Server (DIS)

Backend infrastructure for a tagged-document knowledge base: a document-management web UI, an ingestion pipeline (parse → chunk → embed → store), and an **MCP server** exposing the knowledge base as agent-ready tools over Streamable HTTP.

## Workflow
- Spec-Driven Development. Specs at `sdd/specs/`. Load the `spec-driven-development` skill before any implementation phase.
- After merging a change, update the matching backlog checkbox in the README (root macro task, sub-readme detail).
- Do the task asked, then stop. Ask before fixing anything unrequested.
- Never commit. Only propose one-liner conventional commit messages (`feat: ...`, `fix: ...`, `chore: ...`). No body, no multi-line messages. The user does all commits.
- Never use subagents, do the work direclty.
- **Code exploration**: use `codegraph_codegraph_explore` first for architecture, code flow, or symbol questions — it's faster and more accurate than grep/find/read loops.

## Quick commands
- `make lint`: lint backend + frontend
- `make test`: run all tests
- `make build`: build Docker images
- `make start` / `make stop`: docker compose up/down
- `make logs`: follow service logs

## Layout
- `backend/`: FastAPI app (REST + ingestion) + MCP server, see `backend/AGENTS.md`
- `frontend/`: React app, see `frontend/AGENTS.md`
- `sdd/`: specs and change folders
- `REQUEST.md`: original assignment

<!-- CODEGRAPH_START -->
## CodeGraph

In repositories indexed by CodeGraph (a `.codegraph/` directory exists at the repo root), reach for it BEFORE grep/find or reading files when you need to understand or locate code:

- **MCP tool** (when available): `codegraph_explore` answers most code questions in one call — the relevant symbols' verbatim source plus the call paths between them, including dynamic-dispatch hops grep can't follow. Name a file or symbol in the query to read its current line-numbered source. If it's listed but deferred, load it by name via tool search.
- **Shell** (always works): `codegraph explore "<symbol names or question>"` prints the same output.

If there is no `.codegraph/` directory, skip CodeGraph entirely — indexing is the user's decision.
<!-- CODEGRAPH_END -->
