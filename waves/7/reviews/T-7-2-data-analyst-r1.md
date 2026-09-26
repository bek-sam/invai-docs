# Review of T-7-2 (round 1)

- Reviewer: data-analyst on Sonnet 5
- Author: backend-engineer (finance) + integrations-engineer on Opus 5.5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| Read `invai-backend-review-t72@2d4668f`: `src/modules/finance/fees.ts`, `refunds.ts`, `profit.ts`, `service.ts` (`getProfit`, `refundGroups`, `mergeRefunds`, `orderProfit`), `fees.test.ts`, `refunds.test.ts` | — |
| `node_modules/.bin/vitest run src/modules/finance` (backend worktree, TEST_DATABASE_URL=invai_test_review72) | 9 files / 50 tests passed |
| WebSearch cross-check of Amazon Clothing & Accessories referral schedule | Confirms the fee is a **cliff** (whole sale price at the bracket's rate), not marginal/tax-bracket style — a worked $28 example gives $28×17%=$4.76, matching `referralFeeCents("amazon","apparel",2800)`=476¢ exactly. Also confirms "$14.99 pays 5%, $15.01 pays 10%." |
| WebSearch cross-check of TikTok Shop US referral fee | Confirms 6% flat for fashion in 2026 (the contracts default 8% is stale, as the report says) and a 20%-of-fee refund admin fee capped at $5/SKU — matches `fees.ts` |
| Manual DB-copy check (profit numbers vs. refund total, "by day") | **Not run** — Docker became unresponsive mid-session (see reviewer's file); relying on the DB-backed `refunds.test.ts`/`parse-refunds.test.ts` runs above, which exercise the same `getProfit`/day-view code path against real Postgres |

## Money-math checks
- **Rounding:** every fee/recovery path rounds with `Math.round` on cents (`referralFeeCents`, `feeRecoveredCents`'s `share`/`kept`), never `Math.floor`/`ceil` inconsistently, and the property test `fees.test.ts:129` asserts `Number.isInteger` and non-negativity over 2000 seeded runs. No float leakage found.
- **Amazon $0.30 minimum:** applied after rounding (`Math.max(fee, schedule.minCents)`), correct order of operations; tested at `referralFeeCents("amazon","apparel",400)` = 30.
- **Refund admin fee (20% capped at $5):** `feeRecoveredCents` computes `share` (fee × refunded-share of sale, rounded) then `kept = min(round(share*20/100), 500)`, returns `max(0, share - kept)`. Verified against the report's worked example (28.00 tee, fee 476, full refund keeps min($5, 20%×476=95.2→95) = 381¢ recovered) and matches `fees.test.ts:101-118` exactly.
- **Per-unit fee split reconciliation:** `splitFees` is property-tested (`fees.test.ts:169`) to always sum exactly to the order's fee total across 2000 randomized runs — good protection against a rounding drift across units.
- **Refund dating / period bucketing:** `refundGroups` in `service.ts` reads `refund_events.refundedAt` (not `profit_lines.placedAt`), and both it and the base `getProfit` query now `GROUP BY 1` (the `to_char(...at time zone $1...)` / `$n` GROUP BY mismatch that caused the reported 500 is fixed consistently in both queries) — this was the exact AC2 requirement ("refunds reduce profit on their date") and it's implemented, not just described.
- **Refund cap:** see the blocking finding below — this is the one real gap in the money math.

## Blocking findings
1. Same as the reviewer's file: `invai-backend/src/modules/finance/refunds.ts:127` — `recordRefund` never checks the refund amount against the order's (or item's) sale total or against refunds already booked on it, and there is no edit/delete path. From a pure money-math standpoint, this means a single bad manual entry can push a period's `refunds` bucket arbitrarily past its `revenue` bucket with no bound and no correction — the property tests cover the *fee* math's bounds well, but there's no equivalent bound on the *refund amount* itself. Recommend clamping or rejecting `amountCents` above the order/item's remaining refundable balance before this ships.

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope
- [x] Tests exercise the behavior, none weakened (deferred to reviewer's scan-test-weakening run — no hits)
- [x] Money in cents, property-tested, rounding order correct — except the refund-cap gap above
- [x] Decisions recorded where needed (grant already covered in reviewer's file)

## Optional notes (not blocking)
- Walmart's "no admin fee, returned in full" refund modeling is an honestly-flagged assumption (no source states Walmart's refund behavior); fine to ship with the flag, but worth a real pilot refund to confirm before trusting Walmart profit numbers precisely.
- `CHANNEL_RULES.tiktok.transactionPct` staying at 8 in contracts while `fees.ts` overrides to 6 internally is confusing for anyone reading the settings screen (still shows 8%) — not this card's grant to fix, but flag it moves to the top of whoever owns contracts next.
