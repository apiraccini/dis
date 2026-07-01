# Merge

## Overview

Phase 4: merge delta specs into the main spec files, delete the change folder. No archive.

## Guidelines

- Merge only what's implemented and verified.
- Never merge partial work. All tasks must be checked off.
- After merge, the main specs are the new source of truth.

## Steps

### 1. Verify completion

- All tasks in `sdd/changes/<name>/tasks.md` checked off. Unfinished? Return to Execute. Tasks outdated? Update tasks.md first.
- Lint and the full test suite pass. Red checks block the merge.

### 2. Merge delta specs

For each delta file in `sdd/changes/<name>/specs/`:

- ADDED: append to the corresponding `sdd/specs/<domain>.md`
- MODIFIED: replace the matching requirement in the main spec
- REMOVED: delete the matching requirement from the main spec
- New domain: create `sdd/specs/<new-domain>.md` with the ADDED content

Remove TODO markers resolved by the implementation. Never end up with the same behavior stated twice at different granularities; fold endpoint-level detail into the existing behavioral requirement.

### 3. Delete the change folder

```
rm -rf sdd/changes/<name>
```

### 4. Final check

- `sdd/specs/` reflects the new system behavior.
- `sdd/changes/<name>` no longer exists.
- Any project-level progress tracking, if the project defines one, is updated.
