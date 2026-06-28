# Document Intelligence Server (DIS)

Backend infrastructure for a tagged-document knowledge base: a document-management web UI, an ingestion pipeline (parse → chunk → embed → store), and an **MCP server** exposing the knowledge base as agent-ready tools over Streamable HTTP.

## Workflow
- Spec-Driven Development. Specs at `sdd/specs/`. Load the `spec-driven-development` skill before any implementation phase.
- After merging a change, update the matching backlog checkbox in the README (root macro task, sub-readme detail).
- Do the task asked, then stop. Ask before fixing anything unrequested.
- Never commit. Only propose one-liner conventional commit messages (`feat: ...`, `fix: ...`, `chore: ...`). No body, no multi-line messages. The user does all commits.

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
