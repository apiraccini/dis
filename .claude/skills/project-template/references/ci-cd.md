# CI/CD — GitHub Actions

Two workflow files under `.github/workflows/`. Workflow names are lowercase (`ci`, `cd`); uppercase causes GitHub Actions UI issues.

## CI — `ci.yml`

Runs lint + test for backend and frontend on push and PR to `main`.

```yaml
# .github/workflows/ci.yml
name: ci

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v6

      - name: Set up Python
        run: uv python install

      - name: Install backend deps
        run: uv sync --dev
        working-directory: backend

      - name: Lint backend
        run: uv run ruff check src/ tests/
        working-directory: backend

      - name: Format check backend
        run: uv run ruff format --check src/ tests/
        working-directory: backend

      - name: Type check backend
        run: uv run ty check
        working-directory: backend

      - name: Test backend
        run: uv run pytest
        working-directory: backend

      - name: Setup Bun
        uses: oven-sh/setup-bun@v2

      - name: Install frontend deps
        run: bun install
        working-directory: frontend

      - name: Lint frontend
        run: bun run lint
        working-directory: frontend

      - name: Test frontend
        run: bun run test
        working-directory: frontend
```

- `uv sync --dev` is required: ruff and ty are dev dependencies; without `--dev` CI fails with "command not found".
- Lock files (`uv.lock`, `bun.lock`) must be committed or installs are not reproducible.

## CD — `cd.yml`

Deploys on a VPS via SSH. Gated on CI via `workflow_run`: it fires only after the `ci` workflow completes on `main`, and the job runs only if CI succeeded — a red CI never deploys. Manual runs via `workflow_dispatch` bypass the gate. Skips gracefully when secrets are not configured. If the target VPS is not yet available (e.g. client-owned, secrets pending), comment out the deploy steps and leave a placeholder echo so the workflow stays green.

```yaml
# .github/workflows/cd.yml
name: cd

on:
  workflow_run:
    workflows: [ci]
    types: [completed]
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    if: ${{ github.event_name == 'workflow_dispatch' || github.event.workflow_run.conclusion == 'success' }}
    steps:
      - name: Deploy on VPS
        if: ${{ secrets.VPS_HOST != '' && secrets.VPS_USER != '' && secrets.VPS_SSH_KEY != '' }}
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd <repo-path-on-vps>/${{ github.event.repository.name }}
            git pull
            cat > .env <<'EOF'
            ${{ secrets.ENV_FILE }}
            EOF
            docker compose build
            docker compose up -d
            docker image prune -f

      - name: Skip deploy (no secrets configured)
        if: ${{ secrets.VPS_HOST == '' || secrets.VPS_USER == '' || secrets.VPS_SSH_KEY == '' }}
        run: echo "CD not configured. Set VPS_HOST, VPS_USER, VPS_SSH_KEY secrets to enable deployment."
```

- `workflow_run` triggers only for workflows on the default branch; the `branches: [main]` filter matches the branch CI ran on.
- `docker image prune -f` keeps dangling build layers from filling a small VPS disk.

## Environment file from secrets

Production env vars live in a single `ENV_FILE` GitHub secret holding the complete `.env` content (same keys as `.env.example`, production values). The deploy step writes it to `.env` on every deploy, so the VPS never needs manual env editing and rotating a value is: update the secret, rerun `cd`. Secret values are masked in action logs.

If you prefer to manage `.env` by hand on the VPS instead, delete the `cat > .env` heredoc from the script and skip the `ENV_FILE` secret.

## Required GitHub secrets

| Secret | Value |
|--------|-------|
| `VPS_HOST` | VPS IP or hostname |
| `VPS_USER` | deploy user on the VPS |
| `VPS_SSH_KEY` | private SSH key authorized for that user |
| `ENV_FILE` | full production `.env` content (multiline) |

## VPS-side prerequisites

- Docker and Docker Compose installed.
- The repo cloned at the path used in the deploy script.
- The deploy key authorized for SSH access.
- `.env` is written by the deploy script from the `ENV_FILE` secret; no manual env setup needed.
