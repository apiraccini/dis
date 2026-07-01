# Systematic Debugging

## Overview

Root cause investigation before any fix. Random fixes waste time and create new bugs. Four phases: investigate, analyse, hypothesise, fix.

## Guidelines

- No fixes without root cause investigation first.
- No identified root cause means no proposed fix.
- Phase 4 requires a failing test that reproduces the bug before fixing.
- System over guesswork: always faster in the long run.

## Steps

### 1. Investigate

- Read error messages completely: line numbers, file paths, error codes.
- Reproduce consistently. Can you trigger it reliably every time?
- Check recent changes: `git log -10`, `git diff`.
- Trace data flow. Where does the bad value originate? Fix at the source, not the symptom.

### 2. Analyse

- Find working examples in the same codebase.
- Compare: what's different between working and broken?
- List every difference, however small. Never assume "that can't matter."

### 3. Hypothesise

- State clearly: "I think X is the root cause because Y."
- Make the smallest possible change to test the hypothesis.
- One variable at a time. Never fix multiple things at once.
- Verify before continuing. Fix didn't work? Form a new hypothesis.

### 4. Fix

- Write a failing test that reproduces the bug (TDD RED step).
- Implement the fix: address the root cause, not the symptom.
- One change at a time. No "while I'm here" improvements.
- Verify: test passes, full suite green.
- Keep the regression test in the suite; it prevents recurrence.

### Rule of three

Tried 3+ fixes and none worked? STOP. Question the architecture. Discuss with the user before attempting more. Three failures indicate a wrong architecture, not a wrong hypothesis.
