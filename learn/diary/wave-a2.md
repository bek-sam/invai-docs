# Wave A2 — analytics v2, screens, assistant and digest

**Dates:** 2026-09-30 to 10-01.

## What was built
- **T-A10** A2 contract: D9–D13, action kinds, `today.actions`, `today.recordActionClick`
  (architect): the contract additions every screen in this wave reads from or writes to.
- **T-A6** Profit v2 screens + fixed-cost setting (web-engineer): the owner-facing screens
  for T-A3's finance analytics.
- **T-A8** Assistant tools v6, prompt v6, evals (ai-engineer): the assistant gets analyst
  tools over the new analytics data, with its own eval set.
- **T-A9** Digest D9–D13, D2 mover, Today actions service + click table
  (backend-engineer/digest, today): the digest learns to surface analytics-driven facts,
  and Today gets a real, trackable action-click history.
- **T-A7** Operations, Inventory health, Designs lifecycle, Today panel (web-engineer):
  the remaining screens, plus the Today panel pulling it together.

## Why
Wave A1 built the data; this wave is where the owner actually sees it — profit, operations
and inventory health on screens, up to 5 ranked actions on Today, a digest that catches
shipping loss, losing orders, stock problems, blank price rises and break-even pace, and
an assistant that can explain "why" with real numbers behind it.

## What went wrong
- The shared `invai_test` database collision happened for a **third** time in the
  project's history (after wave 22 and T-23's push-gate issue): parallel agents on T-A9
  collided on it again — the build run's first attempt failed 8 files with foreign-key
  errors, and the reviewer's own run failed 3 more. The lesson log is blunt about why a
  written rule kept not being enough: "a written rule (pin your own DB) depends on every
  prompt and agent following it; the test setup itself shares one DB by default." This is
  the point where the fix stops being a rule and becomes structural — every test run gets
  its own DB and Redis DB unless one is explicitly set (B-228,
  `invai-backend/src/test/global-setup.ts`).
- The contract card (T-A10)'s new enum values broke two backend exhaustive maps the plan
  review hadn't listed, so backend typecheck stayed red until the next card picked it up.
  The plan review had checked web's exhaustive `switch` statements for new enum values,
  but not the backend's `Record<Enum, …>` maps or duplicated key lists.
- An acceptance criterion added to a *running* card (T-A7's AC9) was missed by the
  builder and only caught in review — agents read their card once at the start, and the
  tech lead has no way to message a running agent mid-card.

## What the team learned
- "Pin your own test DB" is the last time this project tries to solve a shared-resource
  collision with a written reminder alone — see module 10.3 for the full five-incident
  arc this closes. From here, isolation is the test framework's default behavior, not an
  instruction.
- When a contract adds new enum values, the plan review now greps every repo for
  exhaustive `switch` statements, `Record<…>` maps and copied key lists, and names each
  one on a card explicitly — not just the obvious consumer-side switches.
- New acceptance criteria don't get added to a card that's already running; they queue
  for the next round's prompt, recorded in the wave log, because a running agent can't be
  reached any other way.

## Files to look at
- `invai-contracts/src/contract/today.ts` (`actions`, `recordActionClick`) — T-A10.
- `invai-web/src/routes/_app/profit.tsx` — Profit v2 and fixed-cost setting (T-A6).
- `invai-backend/src/modules/ai/assistant-tools.ts` (v6) — T-A8.
- `invai-backend/src/modules/digest/`, `src/modules/today/service.ts` — D9–D13, D2 mover,
  the action-click table (T-A9).
- `invai-web/src/routes/_app/{operations,inventory,catalog/designs}.tsx`,
  `_app/index.tsx` (Today panel) — T-A7.
- `invai-backend/src/test/global-setup.ts` — the structural per-run DB isolation (B-228).
- `invai-docs/team/lessons.md` (2026-09-30/10-01, "wave A2" rows, three of them).
