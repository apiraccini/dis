# Spec Format

## Overview

Canonical format for `sdd/specs/<domain>.md` files and delta specs in change folders. Two levels: requirement plus optional scenario. Same format everywhere: bootstrap, plan, merge, sanitize.

## Format

```
- **Requirement: [name]** — SHALL/MUST [observable behavior]
  - Scenario: [name] — GIVEN [context], WHEN [action], THEN [expected outcome]
```

## Guidelines

- Requirements describe what, not how. No library names, class names, file paths, or code flow.
- One observable behavior per requirement, stated once. No behavioral plus endpoint-level duplicates.
- Scenarios are optional but preferred for non-trivial or conditional behavior.
- Keep scenario text compact: "Authenticated user accesses protected resource", not three sentences.
