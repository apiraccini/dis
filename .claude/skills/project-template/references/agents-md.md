# AGENTS.md and README.md Templates

Each level (root, backend, frontend) has an AGENTS.md and a README.md with distinct jobs.

- AGENTS.md: agent-facing. How to work on the project: guidelines, skills to load, tooling, quick commands, rules.
- README.md: human-facing. Overview, stack, tree structure, development, deployment, backlog. Agents read it too, so keep it accurate.
- Style for both: short, information-dense, actionable. One-liner bullets with sub-bullets, no filler, no decoration.
- A root `CLAUDE.md` contains a single pointer line to `AGENTS.md`.

## Root `AGENTS.md`

```markdown
# <Project name>

One-paragraph description of what the app does.

## Workflow
- Spec-Driven Development. Specs at `sdd/specs/`. Load the `spec-driven-development` skill before any implementation phase.
- After merging a change, update the matching backlog checkbox in the README (root macro task, sub-readme detail).
- Do the task asked, then stop. Ask before fixing anything unrequested.
- Commits: one-liner conventional commits (`feat: ...`, `fix: ...`, `chore: ...`). No body, no multi-line messages.

## Quick commands
- `make lint`: lint backend + frontend
- `make test`: run all tests
- `make build`: build Docker images
- `make start` / `make stop`: docker compose up/down
- `make logs`: follow service logs

## Layout
- `backend/`: FastAPI app, see `backend/AGENTS.md`
- `frontend/`: React app, see `frontend/AGENTS.md`
- `sdd/`: specs and change folders
```

## Backend `backend/AGENTS.md`

```markdown
# Backend — <project name>

## Stack
- FastAPI (async), SQLModel, pydantic-settings, PostgreSQL via asyncpg
- uv for Python management, ruff + ty for lint/types, pytest for tests
- Clean architecture: endpoints → services → repositories (Protocol)
- JWT auth in `src/core/security.py`
(- Alembic migrations: only if included)

## Quick commands
- `cd backend && uv sync --dev`: install deps including dev tools
- `uv run uvicorn src.main:app --reload`: dev server
- `uv run pytest`: tests
- `uv run ruff check src/ tests/`: lint
- `uv run ty check`: type check
(- `uv run alembic upgrade head`: migrations, only if included)

## Rules
- Async everywhere, no sync DB access.
- No business logic in endpoints; call services.
- Repositories expose `typing.Protocol` interfaces for mocking.
```

## Frontend `frontend/AGENTS.md`

```markdown
# Frontend — <project name>

## Stack
- React + Vite + TypeScript
- Bun (package manager), Biome (lint + format), Vitest (tests)

## Quick commands
- `cd frontend && bun install`: install deps
- `bun run dev`: dev server
- `bun run build`: production build
- `bun run lint`: biome check
- `bun run test`: vitest
```

## README.md content

- Root `README.md`: project overview, quick start (make targets), `## Backlog` with Backend / Frontend macro-task lists (bare checkboxed bullets, one per SDD session).
- `backend/README.md` and `frontend/README.md`: description, stack, tree structure with one-liner comments, development notes, expanded backlog (each macro task with nested one-liner sub-bullets).
- Never duplicate backlog detail between root and sub-readmes.

## Reminders

- Quick commands always use `uv sync --dev`; without `--dev`, ruff and ty are missing.
- ty runs as `uv run ty check`, never `ty src/`.
- Keep structure trees in sync with the real tree whenever files are added.
