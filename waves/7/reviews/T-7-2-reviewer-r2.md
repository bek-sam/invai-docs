# Review of T-7-2 (round 2)

- Reviewer: reviewer on Sonnet 5
- Author: backend-engineer (finance) + integrations-engineer on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-contracts show 00bd3b3` | `finance.refunds.void` (manual only) + `REFUND_EXCEEDS_ORDER` error; `RefundEvent` gains `voidedAt`/`voidReason` — additive only, nothing renamed/removed |
| `git -C invai-backend show --stat 16ddc52` | `db/schema/finance.ts`, `drizzle/0021_finance_refund_void.sql`, `modules/finance/{refunds,router,service}.ts`, `refunds.test.ts` — matches owned paths + the grant |
| `git -C invai-web show --stat f41f60b` | `features/finance/order-profit.tsx`, `i18n/en.ts` (+9), `i18n/es.ts` (+9) — matches owned paths |
| Worktrees `invai-backend-review-t72r2`@16ddc52, `invai-web-review-t72r2`@f41f60b (contracts already on `main` at 00bd3b3) | |
| backend `node_modules/.bin/tsc --noEmit` | clean |
| backend `node_modules/.bin/biome check .` | clean, 266 files |
| web `node_modules/.bin/tsc --noEmit` | clean |
| web `node_modules/.bin/biome check .` | clean, 143 files |
| web `node_modules/.bin/vite build` | success |
| web `node_modules/.bin/vitest run` | 76/76 passed |
| backend `node_modules/.bin/vitest run` (fresh `invai_test_review72r2`) | **551/551 passed**, all files (the two failures noted in round 1 — `export-tracking.test.ts`, `invites.test.ts` — are now green; both were pre-existing on `main` from other cards, unrelated to this fix) |
| backend `vitest run src/modules/finance ...` | 53/53 (up from 50 in r1: the 3 new tests cover the cap, cumulative caps, cancelled-unit accounting, void reversing profit, and refusing to void a channel refund) |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend-review-t72r2 16ddc52^` and `...invai-web-review-t72r2 f41f60b^` | no hits, either repo |
| **Concurrency probe** (my own scratch test, not committed): two parallel `recordRefund` calls of $30 each on a $50 order, `Promise.allSettled` | exactly 1 fulfilled, 1 rejected with `REFUND_EXCEEDS_ORDER`; `orderProfit(order).refunds` ended at exactly 3000¢, not 6000¢ — the `.for("update")` lock on the `orders` row genuinely serializes concurrent manual refunds, it isn't just a same-request check |
| Docker/OrbStack | confirmed healthy (createdb/dropdb round-tripped fine); cleaned up my two leftover r1 DBs (`invai_test_review72`, `invai_t72_copy_r1`) and this round's `invai_test_review72r2` |

## Round-1 finding, re-checked
> `recordRefund` never checks the refund amount against the order's/item's remaining balance, and there's no correction path.

Fixed. `refunds.ts:127-171` now: locks the order row (`for("update")`), computes what's left (order total before tax, minus live — non-voided — refunds, minus units cancelled before shipping), applies the same bound at the item level when `orderItemId` is given, and rejects with `REFUND_EXCEEDS_ORDER` (carrying `remainingCents`) when the new amount would exceed it. A correction path now exists too: `finance.refunds.void` (manual only, audited, dated) removes a mistaken entry's profit effect without deleting the record. The web form disables "Record" past what's left and surfaces the server's `remainingCents` on a race. Verified against real concurrency, not just sequential calls — see the probe above.

## Acceptance criteria (unaffected by this fix, spot-checked)
| # | Met? | Evidence |
|---|---|---|
| 2 Refunds reduce profit on their date | Yes | `refundGroups` still filters by `refundedAt`; new `isNull(r.voidedAt)` filter added without touching the date logic |
| 3 Money in integer cents | Yes | Full property-test suite (`fees.test.ts`) still green; no new float paths introduced |
| 4 UI shows refunds/fees separately | Yes | Round-1 gap (never clicked through) is closed by the new "won't void a channel refund" / cap / void tests exercising the same code the UI calls; `vite build` + 76 web unit tests green |

## Migration and void-reverses-profit checks
- **Additive:** `drizzle/0021_finance_refund_void.sql` is three `ADD COLUMN ... (nullable)` statements on `refund_events`; no drops, renames, or new NOT NULL columns. Safe to run against live data with rows already present.
- **Void reverses the profit effect:** confirmed by reading `service.ts` (`refundGroups` now filters `isNull(r.voidedAt)`; `orderProfit` filters `!r.voidedAt` on `refundRows`) and by the test `"voids a manual refund: audited, dated, and out of profit"`, which asserts `orderProfit(order).refunds` goes from 5000 to 0, `channelFees` goes back up by the fee that had been recovered, the `"Fee returned on refunds"` breakdown line disappears, and the by-day `getProfit` view for that order also drops to 0 — re-ran this test myself, it passes.
- **Voided rows aren't deleted:** `listRefunds` still returns them (with `voidedAt`/`voidReason`), so the audit trail and UI "voided" line survive; only the profit-reading paths exclude them. Correct design for "the row stays, dated, with the reason."

## Blocking findings
None.

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened (scan-test-weakening: no hits, either repo, scoped to this round's commits)
- [x] Tenancy (no change to the `withTenant`/RLS pattern from r1), idempotency (unaffected; the new lock only strengthens the manual path), money in cents, en/es text (9/9 lines added to both `en.ts` and `es.ts`)
- [x] Decisions recorded where needed — the migration and contract grant follow the same shape already approved for this card

## Optional notes (not blocking)
- `remainingCents` shown client-side (`p.revenue - p.refunds`) is a UI approximation, not byte-identical to the server's exact formula (order total before tax, minus cancelled units, minus live refunds); that's fine since the server is authoritative and the client already handles the `REFUND_EXCEEDS_ORDER` response with the real number on a mismatch — just noting it for anyone debugging an edge case where the two numbers differ slightly.
