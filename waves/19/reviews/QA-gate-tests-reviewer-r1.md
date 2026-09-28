# Review of QA gate test commits (wave 19 integration gate), round 1

- Reviewer: reviewer on Sonnet 5
- Author: qa-engineer (Fable 5.1)
- Verdict: approve

Scope: two QA-owned test commits made during the wave 19 gate (`invai-docs/waves/19/reviews/gate.md`
issue 7), reviewed per operating-system "Who reviews whom" (QA test code → reviewer).
- `invai-web` `49b22c9` — `e2e/digest.spec.ts` selector fix.
- `invai-backend` `5a443ed` — new `src/modules/market/market-scale.acceptance.test.ts` (AC28).

## Evidence I re-ran

| Command | Result |
|---|---|
| `git -C invai-web show --stat 49b22c9` | 1 file, `e2e/digest.spec.ts`, +13/-9 |
| `git -C invai-backend show --stat 5a443ed` | 1 file, new `src/modules/market/market-scale.acceptance.test.ts`, +148 |
| `node_modules/.bin/vitest run src/modules/market/market-scale.acceptance.test.ts` (invai-backend, no `MARKET_SCALE` set) | `1 skipped (1 test file), 1 skipped (1 test)` — did not run the scale test itself |
| `pnpm exec tsc --noEmit -p .` (invai-backend) | clean, no output |
| `pnpm exec biome check src/modules/market/market-scale.acceptance.test.ts` (invai-backend) | "Checked 1 file... No fixes applied" |
| `pnpm exec biome check e2e/digest.spec.ts` (invai-web) | "Checked 1 file... No fixes applied" |
| `pnpm exec tsc --noEmit -p .` (invai-web) | clean, no output |
| Read `src/components/digest/insight-card.tsx`, `src/routes/_app/digests/$weekKey.tsx`, `src/components/market/recommendation-card.tsx` | Confirmed only the `actions` section renders `AnyLink`s with `digestActionText`; `marketWatch` items with `detector: "market"` render `RecommendationCard`, which uses `<Button>`, not links — so the new link selector can't be re-inflated by market-watch items the way the old button selector was |
| Read `src/components/digest/digest-copy.ts` (`digest.action.*` keys) | 2 of 9 action kinds (`seeWhatChanged`, `seeReprints`) start with "See", not matched by the verb regex — pre-existing gap, not introduced by this fix (see note below) |
| Read `invai-docs/build/qa-report.md` AC28 section (lines 210-219) | Confirms the new test's own scope claim: only demand-refresh + signal-compute timing is proven; "k6 tool-latency and EXPLAIN parts of the plan below are still open" — disclosed, not hidden |
| Read `invai-backend/src/modules/digest/scale.test.ts` (precedent) and `src/env.ts` (`TEST_DATABASE_URL`/`TEST_MIGRATION_DATABASE_URL`) | New test follows the same established opt-in-scale-test convention: no in-test cleanup, relies on the operator pointing `TEST_DATABASE_URL`/`TEST_MIGRATION_DATABASE_URL` at a scratch DB (gate used `invai_t19_qa_scale`, dropped after per gate.md §Processes) |
| Did not run `MARKET_SCALE=1 vitest run ...` myself (per instructions) | n/a |

## Acceptance criteria (for this mini-review)

| # | Met? | Evidence |
|---|---|---|
| Selector fix doesn't weaken the test — still asserts exactly the ranked action links, ≤3, wouldn't pass if actions were missing | Yes | New assertion adds a lower bound (`toBeGreaterThanOrEqual(1)`) the old test lacked; `getByRole("link", ...)` isolates the `digest.actions` block's `AnyLink`s from the thumbs/vote buttons that inflated the old count to 10 (gate.md §4); confirmed via component read that market-watch items don't render matching links. The feedback assertion (`downvote` click → "Not relevant") is now unconditional, fixing a prior silent no-op (the old `/thumbs up|👍/` guard never matched real markup, per gate.md §4) |
| AC28 scale test measures what AC28 says, with honest timings, cleans up its DB, skipped by default | Mostly yes, with a disclosed gap | Measures the 15-min budget for `refreshDemand` + `computeSignalsForShop` at 5,000 designs / 3 years / ~1,070 units-day, matching AC28's first half (spec `market-signals.md` line 268). AC28's second half ("each tool answers within 500ms p95 with ≤20 rows") is **not** exercised by this test — but the test's own docstring and `qa-report.md` say so plainly ("k6 tool-latency ... still open"), so this is an honest partial, not a false claim. DB cleanup follows the existing `digest/scale.test.ts` convention (scratch DB via env override, dropped by the operator, not by the test) — same pattern already accepted in this repo. Skipped by default: verified above |
| typecheck/lint clean | Yes | tsc and biome clean in both repos for the touched files |

## Blocking findings

None.

## Checks

- [x] Only owned paths changed (`git diff --stat`) — QA's own test files in both repos
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened — both changes strengthen assertions (added lower bound on action count; made the feedback-thumbs assertion actually run instead of silently skipping); no `.skip`/`.only`, no loosened assertions, no mock of the unit under test
- [x] Tenancy (`withTenant`, RLS on new tables), idempotency, money in cents, en/es text — market-scale test uses `withSystem` only to seed fixture data then calls the real per-tenant functions (`computeSignalsForShop(c.id, ...)`); no new table, no RLS concern; money fields use cents (`4998`, `2499 + ...`) consistent with convention; second-run assertion (`again.recommendations` = 0, not slower) checks idempotency of signal computation
- [x] Decisions recorded where needed — none needed; this is test-only, opt-in, following an existing pattern (`digest/scale.test.ts`)

## Optional notes (not blocking)

1. `e2e/digest.spec.ts`'s verb regex (`^(Ship|Reconnect|Review|List|Reorder)\b`) doesn't match two existing action-text kinds (`digest.action.seeWhatChanged` → "See what changed", `digest.action.seeReprints` → "See reprints", `src/components/digest/digest-copy.ts`). If either ever ranks into the seed's top-3 actions, the link count would undercount and the test could still pass (1–3 in range) while silently missing an action link. This is a pre-existing gap carried over from the old regex (which had the same verb list), not introduced by this commit, and the current seed's 3 actions (Ship/Reorder/Reorder) don't hit it. Not blocking; worth widening the regex or asserting against `d.actions.length` from the API response in a future round.
2. `market-scale.acceptance.test.ts` proves only the compute-budget half of AC28. The tool-latency/row-cap half (500ms p95, ≤20 rows) stays untested at scale, as the author's own `qa-report.md` entry says. Since this is disclosed rather than claimed, it's not a blocking finding here, but the tech lead should track it as an open follow-up (it already is, per qa-report.md's "still open" note) so it isn't lost before a real pilot.
