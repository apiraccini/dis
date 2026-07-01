# Pre-commit Configuration

Uses **prek** — a fast, single-binary Rust drop-in replacement for pre-commit
(j178/prek). Same `.pre-commit-config.yaml` format, adopted by FastAPI / CPython /
Airflow. `pre-commit` still works if preferred; only the install command differs.

## Hooks

```yaml
# .pre-commit-config.yaml
repos:
  # Python: ruff (lint + format)
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.20            # bump via `prek autoupdate`; revs go stale
    hooks:
      - id: ruff-check       # the `ruff` hook id is deprecated since v0.12
        args: [--fix]
      - id: ruff-format

  # Python: ty (type checking via local uv)
  - repo: local
    hooks:
      - id: ty
        name: ty
        entry: bash -c 'cd backend && uv run ty check'
        language: system
        types: [python]
        pass_filenames: false

  # General: base hooks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0             # bump via `prek autoupdate`
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
        exclude: 'tsconfig.*\.json'  # tsconfig files are jsonc with comments
      - id: check-added-large-files

  # Frontend: Biome (lint + format) — local hook for monorepo reliability
  - repo: local
    hooks:
      - id: biome-check
        name: biome check
        entry: bash -c 'cd frontend && bun biome check --write src/'
        language: system
        types: [text]
        files: ^frontend/src/
        pass_filenames: false
```

- The ty invocation is `uv run ty check`, never `ty .`. In a monorepo the hook must cd into `backend/` first, since the venv and pyproject live there.
- Biome runs as a **local hook that cd's into `frontend/`**, mirroring the ty pattern. This is the reliable monorepo approach: the remote `biomejs/pre-commit` hook with `--config-path frontend/biome.json` hits a "Found a nested root configuration" error (biomejs/pre-commit#86) because Biome sees both the repo root and the nested config as roots. Scoping `files` to `^frontend/src/` avoids scanning `public/` assets (SVGs flag accessibility rules) and matches the project's `lint` script.
- If using the remote `biomejs/pre-commit` hook in a single-repo (non-monorepo) setup: its tags track the **Biome tool version** (e.g. `rev: v2.5.1` matches `@biomejs/biome@2.5.1`), NOT independent semver — there is no `v2.0.0` tag. Pin `additional_dependencies: ["@biomejs/biome@<exact version>"]` to the version in `frontend/package.json`; an unpinned hook pulls latest Biome, whose config schema may reject the project's biome.json. The hook's built-in entry already includes `--files-ignore-unknown=true --no-errors-on-unmatched`.
- tsconfig files are jsonc (allow comments); `check-json` rejects them — exclude `tsconfig.*.json`.

## Setup

```bash
cd <project-root>
prek install                # or: pre-commit install
prek autoupdate             # bump revs above to latest; the pins in this doc go stale
prek run --all-files        # initial verification, fix anything it flags
```

After `autoupdate`, re-check that any remote biome hook's `additional_dependencies` still matches the `@biomejs/biome` version pinned in `frontend/package.json` (the local-hook approach above sidesteps this entirely).

prek install: `curl -LsSf https://prek.j178.dev/install.sh | sh` (or `cargo install prek`).
pre-commit install (fallback): `uv tool install pre-commit`.
