# Backend Conventions

## Stack

- Python management: uv (not pip/poetry)
- Framework: FastAPI (async everywhere)
- ORM: SQLModel (async sessions)
- Validation: pydantic + pydantic-settings
- Auth: JWT via PyJWT (OAuth2 password flow, refresh tokens) in `core/security.py`; password hashing via pwdlib (argon2). Not python-jose (abandoned, CVE-2024-33663/33664) or passlib (unmaintained, breaks with bcrypt 4.1+).
- Migrations: Alembic, only when the project has DB model changes
- Type checker: ty (not mypy/pyright)

## Clean architecture (3 layers)

- `endpoints/`: FastAPI routers
  - One file per domain resource (`users.py`, `projects.py`)
  - Thin layer: parse request, call service, format response
  - No business logic, no direct DB access
  - Inject auth and DB session via `Depends()`
- `services/`: business logic
  - One class per domain, stateless
  - Orchestrates repositories, applies rules
  - Accepts a repository in the constructor (injectable, easy to mock)
- `repositories/`: data access
  - Interfaces defined with `typing.Protocol`
  - Implemented with SQLModel async sessions
  - Protocol enables mocking in tests without touching the DB

## Testing

- Framework: pytest + pytest-asyncio
- DB: mock the repository (service tests) or override the session dependency (endpoint tests); no live DB required for the default suite
- Split service tests from endpoint tests:
  - `tests/test_<domain>_service.py`: mock the repository, test business logic in isolation
  - `tests/test_<domain>_endpoints.py`: override `get_session`, test status codes, shapes, auth flows
- Patch with the `monkeypatch` fixture, never by assigning to class attributes (leaks across tests)

## Dependencies (pyproject.toml)

```toml
[project]
dependencies = [
    "fastapi[standard]",
    "sqlmodel",
    "pydantic-settings",
    "alembic",                    # only if migrations needed
    "pyjwt",                      # JWT (not python-jose: abandoned, known CVEs)
    "pwdlib[argon2]",             # password hashing (not passlib: unmaintained)
    "httpx",                      # async HTTP client
    "asyncpg",                    # async PostgreSQL driver
]

[dependency-groups]
dev = [
    "pytest",
    "pytest-asyncio",
    "ruff",
    "ty",
]
```

## Linting

Pre-commit wiring is in `references/pre-commit.md`. Tool-level config in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "SIM", "ARG", "C4", "PT", "RUF"]
ignore = []

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101", "ARG"]

[tool.ruff.format]
quote-style = "single"
indent-style = "space"
line-ending = "auto"

[tool.ty]
```

`[tool.ty]` takes NO fields in current versions. Any key (`quiet`, `verbose`, ...) causes TOML parse errors. Leave it empty or omit it.

## Dockerfile

Multi-stage with uv. The builder needs `uv.lock`; the final stage runs from the venv directly so the uv binary is not needed at runtime.

```dockerfile
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev
COPY src/ src/
RUN uv sync --frozen --no-dev

FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app /app
WORKDIR /app
EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- Always COPY `uv.lock` next to `pyproject.toml`; `uv sync --frozen` fails without it.
- Never use `CMD ["uv", ...]` in a stage that doesn't contain the uv binary.
- If Alembic is included, also COPY `alembic.ini` and `alembic/`.

## Pitfalls

- ty subcommand is `ty check`, not `ty <path>`. `ty src/` fails with "unrecognized subcommand". Applies to CI, pre-commit, and AGENTS.md commands.
- Import `AsyncSession` from `sqlalchemy.ext.asyncio`, never `sqlmodel.ext.asyncio.session`. ty treats the two as different types; standardize on the sqlalchemy import everywhere.
- Use `AsyncSession.execute()`, not `.exec()`. SQLModel's `.exec()` extension is unknown to ty on a bare sqlalchemy session. Use `session.execute(stmt)` + `result.scalar_one_or_none()`.
- Use `datetime.UTC`, not `timezone.utc`. ruff UP017 auto-fixes the latter; write `datetime.UTC` from the start.
- Hatchling + `src/` layout needs an explicit target or `uv sync` fails with "Unable to determine which files to ship":
  ```toml
  [tool.hatch.build.targets.wheel]
  packages = ["src/"]
  ```
- Dev deps use PEP 735 `[dependency-groups]`, the format `uv add --dev` writes. Don't hand-write `[project.optional-dependencies]` for dev tools.
- `uv sync` installs only `[project]` deps. Development and CI need `uv sync --dev`.
- PyJWT's module is `jwt` (`import jwt`); `jwt.encode`/`jwt.decode` always need an explicit `algorithms=["HS256"]` list on decode.
