# TDD — Test-Driven Development

## Overview

Write the test first. Watch it fail. Write minimal code to pass. Refactor. Repeat. If you didn't watch the test fail, you don't know if it tests the right thing.

## Guidelines

- No production code without a failing test first.
- Wrote code before the test? Delete it. Start over. No exceptions.
- One behavior per test. "and" in the test name means split it.
- Test real behavior, not mocks (unless truly unavoidable).
- In GREEN phase: hardcoding, duplication, and cheating are allowed. Refactor later.

## Steps

### 1. RED: write a failing test

- One minimal test for one behavior.
- Clear name: `test_retries_failed_operations_3_times`, not `test_retry_works`.

### 2. Verify RED

- Run the test. Confirm it fails for the right reason (feature missing, not a typo).
- Passes immediately? You're testing existing behavior. Fix the test.

### 3. GREEN: minimal code

- The simplest code that passes. Nothing extra: no logging, no edge cases, no abstractions.

### 4. Verify GREEN

- Run the test. Confirm it passes.
- Run the full suite. Check for regressions.

### 5. REFACTOR: clean up

- Remove duplication, improve names, extract helpers.
- Keep tests green throughout. They fail? Undo immediately.
- Never add behavior here.

### 6. Repeat

Next failing test for the next behavior. One cycle at a time.
