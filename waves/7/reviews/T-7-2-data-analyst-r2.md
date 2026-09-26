# Review of T-7-2 (round 2)

- Reviewer: data-analyst on Sonnet 5
- Author: backend-engineer (finance) + integrations-engineer on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| Read `invai-backend@16ddc52`: `refunds.ts` (`recordRefund`, new `voidRefund`), `service.ts` (`refundGroups`, `orderProfit`) diffs against r1 | — |
| `node_modules/.bin/vitest run src/modules/finance` (fresh `invai_test_review72r2`) | 53/53 passed |
| `node_modules/.bin/vitest run` (full backend suite) | 551/551 passed |
| Own concurrency probe (`Promise.allSettled` of two concurrent $30 `recordRefund` calls on a $50 order) | Exactly one succeeded; the order's total refunded stayed at 3000¢, never 6000¢ |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend-review-t72r2 16ddc52^` | no hits |

## Money-math re-check
- **The cap's formula is right, not just present:** `remaining = max(0, order.totalCents - order.taxCents) - cancelledUnitsSaleCents - sum(live refund amounts)`, and at the item level it's additionally clamped to `unit.saleCents - refunds already on that item`. This correctly accounts for units cancelled before shipping (already booked as refunded in `profit_lines`) so they aren't double-subtracted or missed. The test `"caps manual refunds at what is left on the order and on the item"` exercises all four cases (order-level cap, item-level cap, cumulative multi-call cap, and a cancelled-unit order) with exact `remainingCents` assertions (5000 → 2000 → 0) — I re-ran it and the numbers check out by hand: $50 order, refund $30 leaves $20, refund $20.01 correctly rejected at `remainingCents: 2000`.
- **The race is closed, not just the sequential case:** `SELECT ... FOR UPDATE` on the `orders` row means a second concurrent `recordRefund` blocks until the first transaction commits, then re-reads `listRefunds` (which will see the first's committed row under Postgres's default READ COMMITTED semantics) before computing its own `remaining`. I verified this isn't just true on paper: my own two-concurrent-refunds probe (above) landed at exactly $30 refunded total, not $60 — the lock does its job under real overlapping transactions, not just back-to-back awaited calls.
- **Void's arithmetic reverses cleanly:** `orderProfit`/`getProfit` exclude `voidedAt IS NOT NULL` rows entirely (not zeroed-in-place), so `refunds` and `channelFees` (the fee-recovered credit) both return to their pre-refund values, and the "Fee returned on refunds" breakdown line disappears rather than showing a $0 stub. Confirmed by the test's exact before/after assertions on `orderProfit` and by-day `getProfit`, both green.
- **No new float or off-by-cent path:** the diff touches only integer comparisons (`amountCents > remaining`, all `Cents` types) and adds no new rounding; the existing property tests in `fees.ts` are untouched and still pass.

## Blocking findings
None — the round-1 gap (unbounded manual refund, no correction path) is closed with a formula I can verify by hand and a lock I verified under real concurrency, not just code inspection.

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope
- [x] Tests exercise the behavior, none weakened
- [x] Money in cents, cap formula correct including cancelled-unit and item-level cases, race-safe (verified live), void reverses profit exactly
- [x] Decisions recorded where needed

## Optional notes (not blocking)
- The web's `remainingCents = p.revenue - p.refunds` is an approximation for UI display only (doesn't separately subtract cancelled-unit sale value the way the server does); harmless since the server enforces the real number and the UI already handles a `REFUND_EXCEEDS_ORDER` mismatch gracefully.
