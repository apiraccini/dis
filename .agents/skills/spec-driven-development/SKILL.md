---
name: spec-driven-development
description: "Use when implementing features, fixes, or refactors in a project with (or that should have) an sdd/ directory. Structures work as brainstorm → plan → execute → merge with persistent specs as source of truth."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [sdd, specs, development, workflow, tdd, debugging]
    related_skills: []
---

Persistent specs at `sdd/specs/` are the source of truth for system behavior. Every change goes through 4 phases. Specs are updated as work progresses, never retrofitted.

## Guidelines

- Load only the reference for the current phase. Always load it; never work from memory. Don't read ahead.
- No `sdd/` directory at root? Start with Bootstrap.
- Update specs as understanding deepens; they are living documents.
- References are self-contained. SKILL.md dispatches; references execute.
- Keep it lean: bullets over prose, two-level spec format, no verbose scenarios.
- Skip Bootstrap only; always run Brainstorm and Plan. If `sdd/specs/` exists and covers the domain, skip phase 0, never phases 1 and 2. Every work item gets a change folder.
- Resuming work? If `sdd/changes/<name>/` exists, infer the phase from its artifacts: design.md or delta specs incomplete → Plan; tasks.md with unchecked tasks → Execute; all tasks checked → Merge. Confirm with the user before resuming.
- Don't spec unimplemented domains. Write specs only for code that exists or for a work item the user approved for implementation. No code and no approval means no spec: it would be guesswork. Wait for direction (examples, requirements, POCs).

## Steps

0. [Bootstrap](`references/bootstrap.md`): only if `sdd/` doesn't exist (brownfield). Analyze codebase, propose domains, extract initial specs.
1. [Brainstorm](`references/brainstorm.md`): explore requirements, clarify intent, define scope. No code.
2. [Plan](`references/plan.md`): create the change folder with delta specs, design.md, tasks.md.
3. [Execute](`references/execute.md`): implement. Load as needed during this phase:
   - Writing tests: `references/extra/tdd.md`
   - Hit a bug: `references/extra/debugging.md`
   - Design wrong mid-way: update design.md and delta specs, then continue
4. [Merge](`references/merge.md`): all tasks complete. Merge deltas into main specs, delete the change folder. No archive.

When the user asks to sanitize the specs, load `references/extra/sanitize.md`.
