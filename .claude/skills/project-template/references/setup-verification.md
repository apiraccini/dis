# Setup Verification

Mandatory final step of every scaffold. Two parts: confirm the tooling is installed, then run the full check suite and report honestly.

## 1. Tool installation

Check each tool; install only what is missing.

| Tool | Check | Install |
|------|-------|---------|
| uv | `uv --version` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| bun | `bun --version` | `curl -fsSL https://bun.sh/install \| bash` |
| docker | `docker --version` | https://docs.docker.com/engine/install/ (distro-specific) |
| docker compose | `docker compose version` | ships with Docker Engine plugin |
| prek | `prek --version` | `curl -LsSf https://prek.j178.dev/install.sh \| sh` (or `cargo install prek`) |
| pre-commit (fallback) | `pre-commit --version` | `uv tool install pre-commit` |

- On a fresh VPS or container, docker may need the current user added to the `docker` group.
- Pin nothing here; lock files pin the project, tools track latest stable.

## 2. Repository setup

- `git init` the project and make the initial commit.
- Ask the user for the remote URL. They have one? `git remote add origin <url>` and push. They don't yet? Proceed without; the remote can be added later.

## 3. Post-scaffold checklist

Run from the repo root, in order. Fix failures before moving on.

- [ ] `cd backend && uv sync --dev`: deps resolve, lock file written and committed
- [ ] `cd frontend && bun install`: deps resolve, lock file written and committed
- [ ] `make lint`: ruff check + format check + ty + biome all pass
- [ ] `make test`: pytest and vitest pass (`passWithNoTests` makes empty suites green)
- [ ] `prek run --all-files` (or `pre-commit run --all-files`): all hooks pass (run only, no commits)
- [ ] `make build`: both Docker images build
- [ ] `docker compose up -d` then `curl localhost:8000/health` returns `{"status": "ok"}`; `docker compose down` after
- [ ] Remote configured? Push and confirm CI is green on the first run

## 4. Honest report

A fully green checklist proves the harness works: tooling, lint, test runners, Docker, CI. It proves nothing about the product, because after scaffolding there is zero relevant code.

End the session by reporting to the user:
- What passed and what was fixed along the way.
- An explicit statement that everything beyond the health endpoint is empty scaffolding.
- The backlog as the map of what actually needs building.
