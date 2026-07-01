# Execute

## Overview

Phase 3: implement the change. Follow the four rules below. Call the TDD or debugging protocols as needed.

## Guidelines

- Think before coding. State assumptions explicitly. Present multiple interpretations. Unclear? Ask.
- Simplicity first. Minimum code that solves the problem: no speculative features, abstractions, or configurability, no error handling for impossible scenarios. If it could be 50 lines instead of 200, rewrite it.
- Surgical changes. Touch only what you must. Don't improve adjacent code, comments, or formatting. Match existing style. Every changed line traces to the user's request.
- Goal-driven execution. Transform tasks into verifiable goals. State a plan with verify gates. Strong criteria let you loop independently; weak criteria require constant clarification.

## Steps

### 1. Read tasks

Open `sdd/changes/<name>/tasks.md` and `design.md`. Understand the full picture before touching code.

### 2. Execute each task

For each unchecked task:
- Implement following design.md and tasks.md.
- Verify: tests pass, no regressions.
- Check off the task in tasks.md.

### 3. Validate against design

After each task group, re-read `design.md`. Still aligned? If not, update design.md before continuing.

### 4. Bug during execution?

Load `extra/debugging.md`: systematic root cause investigation before any fix.
