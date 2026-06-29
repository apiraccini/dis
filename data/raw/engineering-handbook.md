# Engineering Handbook

Standards and practices for all engineering teams at Acme Corp.

## Code Review

### PR Requirements

Every pull request must:

- Include a clear description of what and why.
- Pass all CI checks (lint, type-check, tests, build).
- Have at least one approval from a senior engineer.
- Include or update tests for any changed logic.

### Review Etiquette

- Review within 4 business hours during workdays.
- Be constructive, not critical. Suggest alternatives.
- Approve only when you're confident the change is correct.

## Branch Naming

```
<type>/<ticket>-<short-description>
```

Examples:

- `feat/DIS-123-add-ingestion-pipeline`
- `fix/DIS-456-fix-dedup-hash`
- `chore/DIS-789-upgrade-deps`

## CI Pipeline

Our CI runs on GitHub Actions with three stages:

1. **Lint** — ruff, ty, and prettier checks. Must pass in under 2 minutes.
2. **Test** — pytest with coverage ≥ 85%. Integration tests use a service container.
3. **Build** — Docker image build and push to our registry.

## Commit Messages

Use conventional commits:

```
feat: add document dedup by content hash
fix: correct timestamp timezone handling
chore: bump qdrant-client to 1.13.0
```

No multi-line bodies. If you need more detail, put it in the PR description.

## Staging Deploy

Every merge to `main` automatically deploys to the staging environment. Production deploys are manually triggered via a GitHub Actions workflow dispatch.
