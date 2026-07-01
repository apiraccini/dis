# Bootstrap

## Overview

Initialize SDD on an existing codebase (brownfield). Analyze the project, identify logical domains, propose them to the user, extract current behavior into specs. Runs once per repo.

## Guidelines

- Specs describe what the system does, not how it's implemented.
- Domains are logical groupings: auth, payments, search, notifications.
- Start broad, split later if a domain grows too large.
- Can't infer a domain confidently? Flag it as uncertain for the user.

## Steps

### 1. Analyze the codebase

Walk the project structure:
- Entry points, routers, API endpoints, CLI commands
- Module/package organization
- Configuration files, database schemas, environment variables
- Tests (they document behavior by example)

### 2. Identify candidate domains

Group capabilities into logical domains. Each domain maps to one `sdd/specs/<domain>.md`.

Examples:
- `auth`: login, registration, sessions, permissions
- `api`: endpoints, rate limiting, versioning
- `payments`: checkout, billing, subscriptions
- `workers`: background jobs, queues, cron

### 3. Propose to the user

> Analysis of the codebase suggests these domains:
> - auth: JWT auth, session management, RBAC
> - api: REST endpoints, pagination, error formatting
> - payments: Stripe integration, webhooks, invoices
>
> Does this look right? Any I'm missing or should merge?

Wait for user approval before proceeding.

### 4. Create the structure

```
sdd/
├── specs/
│   ├── domain-1.md
│   └── domain-2.md
└── changes/
```

### 5. Extract initial specs

For each approved domain, read the relevant code and write a compact, high-level spec of current behavior. Follow `templates/spec-format.md`.

- Document only behavior that exists; never speculate on future features.
- No code and no user approval for a domain means no spec file. Specs without code are guesswork; wait for direction.
- Behavior unclear from code? Mark it `TODO: confirm [question]`.
