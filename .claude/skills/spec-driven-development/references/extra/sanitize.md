# Sanitize

## Overview

Periodic cleanup of `sdd/specs/`. Specs accumulate noise: implementation details, stale requirements, verbose scenarios, duplicates. Restore them to clean, high-level behavior descriptions.

## Guidelines

- Implementation details belong in design.md and code, not in specs.
- Specs answer what, not how.
- Library names, class names, file paths, internal code flow: noise. Remove or rephrase.
- A scenario that can be one line stays one line.
- When in doubt, delete. You can always re-add.

## Steps

### 1. Review each domain spec

Open `sdd/specs/<domain>.md`. Check every requirement and scenario.

### 2. Remove implementation leakage

- Library/framework names: "MUST use bcrypt" becomes "SHALL hash passwords"
- Internal function names: "Call validate_token()" becomes "SHALL validate tokens"
- File paths or class names: delete
- Step-by-step code flow: describe the outcome, not the steps

### 3. Remove stale requirements

Requirement no longer true? Remove it.

### 4. Compact verbose scenarios

- "A user who has authenticated and has a valid session token attempts to access a protected resource" becomes "Authenticated user accesses protected resource"
- "GIVEN the user is logged in and has a valid session" becomes "GIVEN user is logged in"

### 5. Remove redundancy

Two requirements covering the same behavior, or the same behavior stated at two granularities (behavioral plus endpoint-level)? Keep one, prefer the more general, fold scenarios in.

### 6. Confirm with user

```
Sanitized auth.md: removed 2 implementation details, compacted 3 scenarios, merged 1 duplicate.
Ready to commit?
```

Wait for approval before committing.
