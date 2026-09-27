# Review of T-17-2 (round 1)

- Reviewer: reviewer on claude-sonnet-5
- Author: ai-engineer on claude-opus-5.5
- Verdict: approve

The ai-engineer is editing T-17-3 files in the same backend tree (uncommitted `src/ai/**`,
`src/modules/ai/service.ts`, `evals/assistant/run.ts` etc. on top of this commit). I reviewed
commit `308d16f` only, using a separate git worktree (`../invai-backend-t17-2-review`, detached at
`308d16f`, `node_modules` symlinked from `invai-backend`) so none of that in-progress work leaked
into typecheck, lint, tests or the weakening scan. The worktree, its test DB (`invai_t172_review`)
and Valkey DB 13 were all removed at the end.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend show 308d16f --stat` | 7 files, all inside owned paths + the granted `evals/baseline.json` line (wave.md Grants, 2026-09-26) |
| `git worktree add ../invai-backend-t17-2-review 308d16f` + symlink `node_modules` | clean checkout, `node_modules/@invai/contracts -> ../../../invai-contracts` intact |
| `node_modules/.bin/tsc --noEmit` | clean |
| `node_modules/.bin/biome check .` | `Checked 296 files … No fixes applied.` |
| `TEST_DATABASE_URL=…/invai_t172_review TEST_MIGRATION_DATABASE_URL=…/invai_t172_review REDIS_URL=…/13 node_modules/.bin/vitest run` | `Test Files 98 passed (98)`, `Tests 706 passed (706)` |
| `vitest run src/modules/ai/assistant-tools.test.ts` | `Tests 18 passed (18)` |
| `NODE_ENV=test node_modules/.bin/tsx evals/run.ts assistant --json` (own DB) | `Cases: 26  Plumbing 26/26 (100%)  Quality 17/17 (100%)`, by-tag counts match the report exactly |
| `bash .claude/skills/independent-review/scan-test-weakening.sh invai-backend-t17-2-review 2add4d6` (T-17-2's actual parent commit, clean worktree) | `Result: no hits` — the same scan against the live `invai-backend` tree (contaminated by T-17-3's uncommitted `vi.spyOn` in `service.test.ts`) had shown a false hit; re-running in the isolated worktree confirms it's unrelated to this card |
| Live exercise: API from the review worktree on `:3151` (mock provider), signed in as `owner@desertbloom.test`, `POST /api/v1/ai/assistant/ask` | "Which designs are rising or falling?" → `tool_call get_design_insights` → `tool_result "Designs Aug 29 – Sep 27: 5 rising, 0 falling, 0 low margin, 5 cross-listing gaps"`, streamed text names Cactus Mama etc. "Am I shipping on time?" → `tool_result "All channels Aug 29 – Sep 27: 100.0% on time, 44 overdue now, 17 reprints"` |
| Hand SQL: `select count(*) filter (where shipped_at <= ship_by), count(*) from orders where company_id = <desert bloom> and shipped_at in [Aug 29, Sep 28) and status <> 'cancelled'` | `262 / 262` — matches the tool's "100.0% on time" exactly |
| Refused case: `presser@desertbloom.test` → `POST /assistant/ask` | `HTTP 403 FORBIDDEN "Missing permission ai.assistant.ask"` |
| `grep -n "tenantPolicy(" src/db/schema/*.ts` for `channel_connections`, `listing_variants`, `ad_spend`, `refund_events`, `profit_lines`, `reprints` | all six have RLS — the backstop for the joins in `get_design_insights`/`get_fulfillment_health` that don't redundantly filter every joined table by `company_id` (a pattern already used elsewhere in this codebase, e.g. `finance/service.ts`) |
| Hand-verified numbers against the test's own fixture, independent of the code under test | see "Correctness, worked by hand" below |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `MAX_ROWS = 20` on every list; "returns no buyer PII and caps every list at 20 rows" walks every array; money in cents and ratios 0..1 throughout `data` (ROAS is a multiplier by definition, not a 0..1 ratio, correctly so per the spec table) |
| 2 | yes | default-previous-period test asserts `previous.from`/`.to` exactly, and the sum invariant is a real assertion: `sum(byChannel.revenueChange) === change.revenue.abs` and same for `netChange`, both hand-verified below |
| 3 | yes | ROAS/TACoS numbers hand-verified below; `attribution: "channel"` present; campaign rows' keys are exactly `campaign/channel/shareOfSpend/spend` (asserted) |
| 4 | yes | rising/falling/low-margin/top-net and cross-listing-gap tests hand-verified below; gaps never name a channel with no connection (`shopify`, disconnected, never appears in `missingOn` — asserted) |
| 5 | yes | on-time rate, median hours, reprint cost and refund numbers hand-verified below and against the live seed |
| 6 | yes | "shop A never sees shop B rows, and B never sees A's" across all 5 call shapes, both directions, plus asserts B's own real totals (not just "empty") |
| 7 | yes | PII-key regex walk over every `data` object/array; plus a literal string check the fixture's `buyerRef`/`buyerNote` values never appear in any tool output |
| 8 | yes | every expected number in the test file is computed by hand in the header comment and per-`it`, from raw inserted rows — not from re-running `getProfit`/the tool's own SQL |
| 9 | yes | mock-routing tests plus live routing exercised above (design + fulfillment questions both routed correctly) |
| 10 | yes | 10 new cases (`as-017`–`as-026`), `as-024` is the hostile-design-name injection case; eval numbers ($190.00, 5.43x ROAS, "Spring" campaign, "Cactus Sunset", "$40.00", 85.7%) hand-checked against `evals/assistant/seed.ts`'s fixture — all correct |
| 11 | yes | `src/ai/ai.test.ts` and `src/modules/ai/service.test.ts` are untouched by this diff; full suite (706/706) green |
| 12 | yes | small-shop test: `get_ad_performance` returns `roas: null`, answer "No ad spend was recorded…"; `compare_periods` handles zero-then-nonzero (`pct: null`, "(new)") and zero-both ("no sales in either period") |
| 13 | yes | `shopify` (disconnected) never in `missingOn`, appears in `inactiveChannels`, `incomplete: true`, reason `channel_not_connected:shopify`, answer says it isn't connected |

## Correctness, worked by hand (independent of the code and the report)
I re-derived these from the raw fixture rows in `assistant-tools.test.ts` and `evals/assistant/seed.ts`, not from running the tool or trusting the report:
- **`get_ad_performance`:** current spend etsy 1000+600=1600, amazon 2500, total 4100; current revenue etsy 4×2500+3×2000=16000, amazon 3×3000=9000, total 25000. ROAS(shop)=25000/4100, amazon ROAS=9000/2500=3.6, amazon TACoS=2500/25000=0.1, etsy ROAS=16000/1600=10, etsy TACoS=1600/25000=0.064 — all match the test's assertions.
- **`getProfit`'s refund merge** (`src/modules/finance/service.ts:985` `refundGroups`, dated by the refund's own `refundedAt`) explains why amazon's `netBeforeAds` is `2300`, not the naive `2700` (3×900): the $400 refund (dated inside the current period) is folded in by the existing, unmodified `getProfit`, which this card correctly reuses rather than re-deriving. `netAfterAds = 2300 − 2500 = −200` → `spend_with_negative_net` flag, no `spend_up_revenue_down` (revenue 9000 is not below previous 6000) — matches.
- **Reprint cost** (`assistant-tools.ts` `reprintCost` SQL): the subquery's `1 + count(other reprints for this item, status <> 'cancelled')` intentionally *includes* the current row, so for an item with exactly one active reprint the denominator is `2` (1 original print + 1 reprint) — `peel`: `2 × (1000 blank + 300/2 transfer) = 2300`; `misprint`: `300/2 = 150` (blank not consumed, cancelled sibling excluded from both the row and the subquery). Total `2450` — matches.
- **On-time rate:** etsy ship hours `[24,24,24,72]` (D1) + `[10,20,30]` (D3) → 1 late (72h > 48h shipBy); amazon `[12,12,60]` → 1 late. `8/10 = 0.8` — matches, and independently reconfirmed live against the shared dev seed (`262/262`, "100.0%").
- **Eval seed (`evals/assistant/seed.ts`):** current-30-day revenue = hostile 4×2500 + cactus 3×3000 = 19000¢ = **$190.00** (the `day(40)` cactus sale falls outside the 30-day window, correctly excluded); ROAS = 19000/(1500+2000) = 5.428… ≈ **5.43**; on-time = 6/7 (the 72h cactus ship is late) = **85.7%**; hostile design net = 4×1000 = **$40.00**, higher than cactus's period net (2700−500 refund = 2200), so it's correctly the top-net design *by its real number*, not the "$1M" its name asks for — this is the actual proof behind the injection acceptance criterion (spec AC8, card AC10's sibling), not just a string-absence check.

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`assistant-tools.ts`, new `assistant-tools.test.ts`, `mock.ts` routing, `evals/assistant/**`, and the granted `evals/baseline.json` assistant-route lines)
- [x] Nothing outside scope. `evals/baseline.json`'s diff also silently re-escapes one *other* route's `skippedReason` string (`—` → `—`, same character, artifact of the JSON writer re-serializing the whole file) — no other route's numbers changed; noted as cosmetic, not blocking
- [x] Tests exercise the behavior; scan for weakening is clean in an isolated worktree at this commit; every new/changed assertion is additive (`removed=0 added=105`)
- [x] Tenancy: every tool runs under `withTenant(ctx.companyId, …)`; every new query filters by `company_id` on at least the row's own table; the tables joined without a redundant `company_id` filter on every side (`reprints`↔`orderItems`/`orders`/`profitLines`, `listingVariants`↔`listings`) all have RLS (confirmed by `tenantPolicy(...)` in schema), matching the existing codebase's pattern elsewhere; the black-box tenant-isolation test (both directions, all 5 call shapes) passed
- [x] Idempotency — n/a, read-only tools, no side effects
- [x] Money in cents throughout; ratios 0..1 where the metric is a ratio (ROAS is correctly a multiplier, not a 0..1 ratio)
- [x] No buyer PII in `data` (regex-scanned every key, plus literal string checks against the fixture's PII values)
- [x] Decisions recorded in the report (TACoS uses total shop revenue so per-channel figures sum to the shop's; net-after-ads uses the real `ad_spend` ledger, not the profit line's ballpark ads allocation) — sound and match spec intent (a per-channel TACoS using channel revenue would just be `1/ROAS`, redundant)

## Optional notes (not blocking)
- `evals/**` sits outside the backend `tsconfig`/`biome` includes (confirmed: `tsconfig.json` `include: ["src"]`, `biome.json` `files.includes` only covers `src/**` and root-level files), so `seed.ts`/`run.ts` are checked only by actually running the eval, as the report says. Pre-existing gap, not introduced by this card — worth a platform-sre/backend-foundation card at some point.
- The reprint-cost subquery's "include the current row" behavior is correct but non-obvious; a one-line comment next to the `1 +` (already partly there: "the item's transfer cost split over its prints") would save the next reader the derivation I had to do by hand.
