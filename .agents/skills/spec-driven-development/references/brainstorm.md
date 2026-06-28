# Brainstorm

## Overview

Phase 1: explore requirements, clarify intent, define scope. No code, no specs yet. Just understand what needs to happen.

## Guidelines

- Resist the urge to design or implement. Stay at the "what" level.
- Challenge assumptions: "why this approach?", "what problem are we solving?"
- State scope boundaries explicitly: in scope vs out of scope.
- User vague? Ask clarifying questions until you can describe the change in one sentence.

## Steps

### 1. Understand intent

Ask or infer:
- What's the user goal? What problem does this solve?
- Who will use it? Under what conditions?
- New feature, bug fix, refactor, or performance improvement?

### 1b. Research technical alternatives

When the change involves a significant technical choice (new dependency, external service, API, provider) — not a choice already established in the codebase — stop and validate:
- Is this the best option, or just the most obvious one?
- Research alternatives: free tiers, rate limits, integration status, known issues.
- Present a compact comparison table and recommend one option.
- Let the user make the final call. Never commit to a design decision without at least one alternative considered.

> Example: "Tavily vs Brave vs DuckDuckGo". Brave won with 2,000 free queries/month vs Tavily's 1,000, plus native LangChain integration and no rate limit issues.

### 2. Define scope

```
In scope:
- [capability A]
- [capability B]

Out of scope:
- [capability C] (future work, separate change)
- [capability D] (not relevant)
```

### 3. Identify affected domains

Which `sdd/specs/<domain>.md` files will this change touch? List them. New domain? Note it.

### 4. Confirm with user

> Intent: add rate limiting to the public API.
> Scope: 3 requests/second per IP, configurable, 429 response.
> Domains: sdd/specs/api.md
>
> Ready to plan?

Wait for the green light, then proceed to Plan.
