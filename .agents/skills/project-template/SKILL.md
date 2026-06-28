---
name: project-template
description: Standard monorepo for personal apps — FastAPI + React + clean architecture
---

Standard monorepo layout for new apps: FastAPI backend, React frontend, Docker Compose, GitHub Actions. References in `references/` hold the per-area conventions.

## Guidelines

- Discuss the design before implementing. Explore architecture, structure, naming, and trade-offs with the user. Ask clarifying questions, propose options with trade-offs, write nothing until the design is agreed.
- Do the task asked, then stop. No scope expansion, no "while I'm here" refactors, no unrequested fixes. Spot something worth fixing? Ask first.
- Clarify component presence during brainstorming. Not every project needs every component.
  - Ask explicitly: database? Migrations (Alembic)? Frontend? Which clean-architecture layers?
  - Mark absent components explicitly so they are not created as stubs and don't appear in AGENTS.md.
  - Default to the full template then trim, rather than assume minimal.
- Alembic is opt-in. Include it only when the project needs DB migrations. If excluded, remove every trace: alembic.ini, alembic/ dir, the dependency in pyproject.toml, COPY lines in the Dockerfile, mentions in AGENTS.md and README.md.
- Commit lock files. `.gitignore` must never exclude `*.lock`. Both `backend/uv.lock` and `frontend/bun.lock` are tracked for reproducible CI.
- Ship a root `.env.example` listing every env var with dev defaults. `.env` stays gitignored; new machines start with `cp .env.example .env`.
- Scaffold ships one real test per side: the backend `/health` smoke test and a frontend render smoke test, so both test runners exercise something from day one.
- Keep the documentation split:
  - AGENTS.md (root, backend, frontend): agent-facing. How to read the project, guidelines, skills to load, tooling, quick commands.
  - README.md (root, backend, frontend): human-facing. Overview, stack, tree structure, development, deployment, backlog. Agents read it too, so keep it accurate.
- README backlog convention. Root `README.md` has a `## Backlog` section with two bullet lists (Backend / Frontend), one bare bullet per macro task (one SDD session's worth). Sub-readmes expand each macro task into nested one-liner bullets. Root overview, sub-readme detail: never duplicate content between the two.
- Finish every scaffold with `references/setup-verification.md`. Mandatory: verify tooling, run the full check suite, and report honestly. Green checks at this stage prove the harness only, since no product code exists yet.

## Structure

```
project/
├── AGENTS.md               # Agent context: guidelines, skills, commands
├── CLAUDE.md               # Pointer to AGENTS.md
├── README.md               # Human overview + backlog
├── .env.example            # Every env var with dev defaults
├── .pre-commit-config.yaml
├── docker-compose.yml
├── Makefile                # lint, test, build, start, stop, logs
├── .github/workflows/      # ci.yml, cd.yml (cd gated on ci via workflow_run)
├── sdd/                    # specs and change folders (spec-driven-development skill)
├── backend/
│   ├── AGENTS.md
│   ├── README.md
│   ├── Dockerfile
│   ├── pyproject.toml      # uv-managed
│   ├── alembic/            # OPTIONAL: only if DB migrations needed
│   ├── src/
│   │   ├── main.py
│   │   ├── core/{config,dependencies,security}.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── endpoints/
│   │   ├── services/
│   │   └── repositories/   # Protocol-based
│   └── tests/
└── frontend/
    ├── AGENTS.md
    ├── README.md
    ├── Dockerfile
    ├── nginx.conf          # SPA serving + /api proxy
    ├── package.json
    ├── biome.json
    ├── vitest.config.ts
    └── src/
```

## References

- `references/backend-conventions.md`: FastAPI, SQLModel, clean architecture, uv, JWT auth, pytest, pyproject.toml configs, Dockerfile
- `references/frontend-conventions.md`: React + Vite + TypeScript, Bun, Biome, Vitest, Dockerfile
- `references/ci-cd.md`: GitHub Actions workflows (CI + VPS deploy)
- `references/agents-md.md`: AGENTS.md and README.md templates for root/backend/frontend
- `references/pre-commit.md`: pre-commit hook config (ruff, ty, base hooks, biome)
- `references/setup-verification.md`: tool installation and mandatory post-scaffold checklist

## Pitfalls

- CI workflow names are lowercase: `name: ci` and `name: cd`. Uppercase causes GitHub Actions UI issues.
- CI needs `uv sync --dev`. Without `--dev`, ruff and ty are not installed and CI fails with "command not found".
- ty runs as `uv run ty check`, never `ty src/`.
- Domain models live in their own file (`models/user.py`), not in `models/__init__.py`. The `__init__.py` only re-exports.
- `typing.TYPE_CHECKING` imports are invisible at runtime. A name from a TYPE_CHECKING block used in a runtime context (e.g. `Annotated[User, Depends(...)]`) needs a string forward reference: `Annotated['User', Depends(...)]`.
