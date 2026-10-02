# Wave 18 — market signals for the assistant

**Dates:** 2026-09-27, pushed 2026-09-27.

## What was built
- **T-18-1** Market contract + ADR 0015, global cache (architect): a new `market`
  procedure group in the contract, plus a decision record for caching market data once
  across all tenants instead of per-shop.
- **T-18-2** Market providers + deterministic mocks (integrations-engineer): outside data
  sources (trend signals, pricing comparisons) with mock providers that behave
  deterministically for tests, same pattern as every other integration.
- **T-18-3** Market module: taxonomy, mapper, signals, rules R1–R5, recommendations, jobs,
  feedback (backend-engineer/market): the actual logic that turns outside signals into
  "which of my designs are trending" and similar recommendations.
- **T-18-4** Assistant market tools, niche route, prompt v5, validator, evals (ai-engineer):
  wires the market module into the assistant so it can answer with evidence.
- **T-18-5** Web: chips, starters, sample-data badge, votes, niche chip (web-engineer): the
  UI, including the "Sample data" badge that marks mock-sourced numbers honestly.

## Why
The wave's own goal names the exact bar: an owner asks "Which of my designs are
trending?", "Am I priced right?" or "When should I get ready for Halloween?" and gets an
answer built only from the shop's own data and compliant sources, with source, date and
confidence on every outside fact, and a fixed action per recommendation. The "Sample
data" badge exists because mock providers are used locally and in demos — the UI must
never let a mock number look like a real one.

## What went wrong
- A guardrail's fail-closed fallback text — the thing shown when the AI call itself fails
  — failed its *own* validator, because mock data was shown without the required "Sample
  data" label. The fallback path had never been tested with mock inputs, only the happy
  path had.
- A request to plant a deliberate "canary" bug into a builder's work (to test whether
  reviews actually catch injected defects) was denied by the session's own permission
  system — asking an agent to knowingly commit a known defect looks like sabotage to the
  permission layer, even when the intent is quality-process testing. This became owner
  inbox item OI-15, unresolved as of this wave.
- The memory-path mistake from waves 16/17 happened a **third** time this wave: memory
  landed in `invai-docs/.claude/agent-memory/` again, because the tech lead's session had
  started inside `invai-docs` and the memory-path guard (which checks `CLAUDE_PROJECT_DIR`)
  failed open under those conditions.

## What the team learned
- "Every fail-closed fallback gets a test that its output passes the validator it falls
  back from" — a fallback path is still a path the product can take, and it needs the
  same acceptance proof as the happy path, not less.
- A third occurrence of the same mistake (memory in the wrong folder) is the signal that
  moves a fix from "tell people again" to "name the exact absolute path in every prompt,
  and have the owner start the tech lead from the right folder" — written rules alone had
  already failed twice by this point.
- Testing the review process itself (via canaries) needs the owner to pick a method before
  the team tries it again — the permission system treating it as sabotage is a feature,
  not a bug to route around.

## Files to look at
- `invai-contracts/src/contract/market.ts`, `invai-docs/decisions/0015-global-market-cache.md` — T-18-1.
- `invai-backend/src/integrations/market/` — T-18-2.
- `invai-backend/src/modules/market/` — T-18-3.
- `invai-backend/src/modules/ai/niche.ts`, `src/ai/**` (prompt v5) — T-18-4.
- `invai-web/src/components/market/` — the Sample data badge (T-18-5).
- `invai-docs/owner-inbox.md` (OI-15) — the canary-planting question.
- `invai-docs/team/lessons.md` (2026-09-27, "Wave 18" rows, three of them).
