# Plan

## Overview

Phase 2: turn intent into delta specs, design, and tasks. Create the change folder with the artifacts that guide implementation.

## Guidelines

- One change folder per logical feature/fix. Never bundle unrelated work.
- design.md merges the "why" (proposal) and the "how" (design) into one lean document.
- Delta specs describe only ADDED, MODIFIED, REMOVED requirements, never the full spec.
- Deltas must not restate an existing requirement at a different granularity. If the main spec already covers a behavior, modify that requirement instead of adding an endpoint-level or implementation-level duplicate.
- Tasks are checkboxes small enough to complete in one sitting, structured for TDD: one testable behavior per task.
- Need the TDD protocol? Load `references/extra/tdd.md`.
- Specs stay compact: single-line requirements with single-line scenarios.

## Steps

### 1. Create the change folder

```
sdd/changes/<kebab-case-name>/
```

### 2. Write delta specs

For each affected domain, create `sdd/changes/<name>/specs/<domain>.md`. Follow `templates/spec-format.md`, with these section headers:

```markdown
### ADDED

- **Requirement: [name]** — SHALL [observable behavior]
  - Scenario: [name] — GIVEN x, WHEN y, THEN z

### MODIFIED

- **Requirement: [name]** — SHALL [new behavior] (was: [old behavior])
  - Scenario: [name] — GIVEN x, WHEN y, THEN z

### REMOVED

- **Requirement: [name]** — (reason for removal)
```

Include only what's changing. Never copy-paste the full existing spec.

### 3. Write design.md

Copy `templates/design.md` into the change folder and fill it out:
- Intent: what problem this solves (from brainstorm)
- Scope: in scope / out of scope
- Approach: technical decisions, architecture rationale
- Affected domains: which specs are touched

### 4. Write tasks.md

Copy `templates/tasks.md` into the change folder and fill it out. Break the work into logical steps, each independently verifiable.

```markdown
## [Group Name]

- [ ] 1.1 [atomic task]
- [ ] 1.2 [atomic task]
```
