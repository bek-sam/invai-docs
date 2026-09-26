# Review of T-7-3 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: backend-engineer on Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend show --stat b04849e` | 3 files: `modules/billing/service.ts` (+10/-5), `modules/shipping/label-fee.test.ts` (new, 159 lines), `modules/shipping/service.ts` (+3/-3) — matches owned paths exactly |
| `git -C invai-backend diff b04849e~1 b04849e -- src/modules/billing/service.ts src/modules/shipping/service.ts` | Read in full; see findings below |
| `git -C invai-docs show --stat 07ecddf` | `calc/cost_model.py` (+2/-2) + report file — matches owned path |
| `git -C invai-docs diff 07ecddf~1 07ecddf -- calc/cost_model.py` | `LABEL_PRICE 0.15 → 0.10`, comment added, printed label now interpolates the live constant |
| `pnpm typecheck` (invai-backend) | clean (`tsc --noEmit`, no errors) |
| `pnpm lint` (invai-backend, biome) | clean, 267 files, no fixes needed |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend b04849e~1` | 0 assertions removed / 6 added; only hit is `vi.mock` of `../../integrations/carriers` (the EasyPost adapter, an external dependency) — the unit under test (`getPlan`, `recordLabel`, `currentUsage`) is never mocked. Not blocking. |
| `pnpm vitest run src/modules/shipping/label-fee.test.ts` | **Not completed** — Postgres refused the connection mid-run (`ECONNREFUSED ::1:5432` / `127.0.0.1:5432`) despite a bare `nc -z localhost 5432` succeeding seconds earlier; a follow-up `psql` probe returned nothing. This matches the author's own report of docker/DB flakiness on this box. Per the task's instruction to keep commands short and not live-run, I did not retry in a loop; see "Static verification" below for how AC1–4 were confirmed instead. |
| Read `src/modules/billing/service.ts:155-166,185-253` (`getPlan`, `currentUsage`) and `src/modules/finance/service.ts:419,587` (`shipments.labelFeeCents` reads) | Confirms the single-write design described below |
| Read `src/modules/tenancy/demo-guards.test.ts` presence and `git show 5339a57 -- src/modules/shipping/service.ts` | Demo guard lives in `carrierAdapter(ctx)` call sites (`rateOrder`, `buyLabel`, `voidShipment`); none of those lines appear in b04849e's diff |

### Static verification in place of the blocked live run
I read the actual diff line-by-line rather than trusting the report:
- `recordLabel` (`shipping/service.ts:882-928`) computes `labelFeeCents = (await getPlan(tx, ctx.companyId)).labelFee` **once**, then writes that same local variable to both the `labels` insert and the `shipments` update. There's no second lookup, so the two rows cannot diverge from a plan change mid-flight or a rounding difference.
- `getPlan` (`billing/service.ts:155-166`) reads `companies.plan`, defaults to `"trial"` when unset, and looks up `PLAN_CATALOG`/`plans` — trial's `labelFeeCents: 0` is unchanged by this diff (only starter/growth/pro/scale moved to `10`).
- `currentUsage` (`billing/service.ts:233-244`) sums `labels.labelFeeCents` for `labelFees` — the same column `recordLabel` just wrote — so billing usage, the labels row and the shipments row are all one write, read three ways. No separate reconciliation code exists that could drift.
- `finance/service.ts:419,587` reads `shipments.labelFeeCents` for the profit calc's shipping cost — same column, same source.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Fee source (`LABEL_FEE_CENTS` gone, uses `PLAN_CATALOG.labelFeeCents`) | Yes | Diff removes the constant; `recordLabel` now calls `getPlan` for the value. `grep -rn "LABEL_FEE_CENTS" invai-backend/src` returns nothing. |
| 2. Default price ($0.10, `// see OI-1`, awaiting owner) | Yes | Each paid plan's `labelFeeCents: 10, // see OI-1`; doc comment above `PLAN_CATALOG` also points at OI-1 and states the three options are still open. Trial untouched at `0`. |
| 3. Consistency (billing usage, labels row, shipments row, profit all agree) | Yes | Single computed value written to both rows (see above); billing usage and finance both read those same columns — no new code needed, as the card anticipated. |
| 4. Tests cover per-plan fees | Yes (by code reading; live run blocked — see above) | `label-fee.test.ts` is `it.each(["starter","growth","pro","scale"])`, asserts `expected = PLAN_CATALOG.find(...).labelFeeCents` lands on `shipment.labelFee`, the `shipments` row and the `labels` row; a second test asserts `currentUsage(...).labelFees` delta equals the plan's fee exactly. These assertions would fail against the pre-diff code (old code always wrote the flat `LABEL_FEE_CENTS=4`, not the plan's own value), so they are real regression tests, not incidental passes. |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`modules/billing/**`, `modules/shipping/service.ts`, tests, `calc/cost_model.py`)
- [x] Nothing outside scope — the three other OI-1/cost-model gaps (AI design cost, Scale $1,499 vs. custom, free-pilot revenue) are correctly left untouched and called out as still open in both the report and the diff
- [x] Tests exercise the behavior, none weakened (scan clean; only an external-carrier mock, not the unit under test)
- [x] Tenancy: no new tables; `getPlan`/`recordLabel` already ran under `withTenant`/an existing `tx` — unchanged by this diff
- [x] Idempotency: label purchase idempotency (carrier call + `onConflictDoNothing`) is pre-existing and untouched
- [x] Money in cents: `labelFeeCents` stays an integer cents column throughout; `getPlan().labelFee` is the same integer, no float introduced
- [x] Demo guard (T-6-5) unaffected: the guard is in `carrierAdapter(ctx)` at `rateOrder`/`buyLabel`/`voidShipment`; b04849e touches none of those lines, only the fee-lookup inside `recordLabel`, which runs after the carrier call and doesn't touch which adapter (mock vs. real) is chosen
- [x] Cost model matches the code: `LABEL_PRICE = 0.10` (dollars) = `PLAN_CATALOG.labelFeeCents = 10` (cents) ÷ 100, comment cross-references the catalog and OI-1, and the printed table now shows the live constant instead of a hardcoded `$0.15` (removes a future drift risk)
- [x] Decisions recorded where needed: OI-1 correctly left open, not answered by this card; report says so explicitly

## Optional notes (not blocking)
- The live DB-backed test run I attempted hit environment flakiness (Postgres refused connections mid-run on this box), consistent with the author's own report of docker hanging during their verification. I'm approving on strong static evidence (the diff, the test assertions, and the exact columns/functions each reads/writes) rather than the author's word alone, per the card's explicit allowance that static checks and unit-test *code* review are sufficient here. A future round should re-run `pnpm vitest run src/modules/shipping/label-fee.test.ts` once the DB is stable, as a sanity check rather than a gate.
- `ensurePlanCatalog()`'s module-level memoization (`catalogSynced ??= ...`) is pre-existing and unrelated to this card, but worth noting for whoever next changes `PLAN_CATALOG` values at runtime in a long-lived process (e.g. a hot-reloaded dev server): the cache is only populated once per process.
