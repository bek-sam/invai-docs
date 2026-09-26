# Review of T-7-2 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: backend-engineer (finance) + integrations-engineer on Opus 5.5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend show --stat 2d4668f` | 14 files: `modules/finance/**`, `integrations/channels/{csv,shopify}/**`, plus granted hunks in `channels/sync.ts` (2 `ingestChannelRefunds` calls) and `integrations/channels/types.ts` (`ChannelRefund`) — matches owned paths + approved grant |
| `git -C invai-web show --stat d9c1e90` | 4 files: `features/finance/order-profit.tsx`, `i18n/en.ts` (+4), `i18n/es.ts` (+4), `routes/_app/analytics/profit.tsx` — matches owned paths |
| worktrees `invai-backend-review-t72`@2d4668f, `invai-web-review-t72`@d9c1e90, `node_modules` symlinked |
| backend `node_modules/.bin/tsc --noEmit` | clean |
| backend `node_modules/.bin/biome check .` | clean, 265 files |
| backend `node_modules/.bin/tsup` | build success (server.js, index.js) |
| backend `node_modules/.bin/vitest run` (TEST_DATABASE_URL=invai_test_review72) | 539/541 passed. 2 failures pre-existing on `main`, not from this commit: `shipping/export-tracking.test.ts` (belongs to T-7-1's `24b6790`) and `tenancy/invites.test.ts` (flaky — passed alone on rerun) |
| backend `vitest run src/modules/finance src/integrations/channels/csv/parse-refunds.test.ts src/integrations/channels/shopify` | 50/50 passed |
| web `node_modules/.bin/tsc --noEmit` | clean |
| web `node_modules/.bin/biome check .` | clean, 143 files |
| web `node_modules/.bin/vite build` | success |
| web `node_modules/.bin/vitest run` | 76/76 passed |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend-review-t72 2d4668f^` | no hits |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-web-review-t72 d9c1e90^` | no hits |
| WebSearch: Amazon Clothing & Accessories referral fee structure | confirms cliff (not marginal) tiers: "$14.99 shirt pays 5%; $15.01 shirt pays 10%"; worked $28 example = $28×17% = $4.76, matches `referralFeeCents("amazon","apparel",2800)` (476¢) exactly |
| WebSearch: TikTok Shop US referral fee 2026 | confirms 6% flat for fashion (8% is stale, matches report) and 20%/$5-cap refund admin fee — matches `fees.ts` |
| DB-copy manual pass (API :3195, web :5195, Redis /13) | **not completed** — Docker/OrbStack became unresponsive mid-session (`docker ps` hangs indefinitely, unrelated to this diff — verified before this review it worked fine for `createdb`). Did not run `orb stop/start` since it would disrupt other agents' shared Postgres/Redis. Substituted with the DB-backed vitest suite above, which already exercises `recordRefund`, the upsert-idempotent ingest path, and the day-view group-by fix against real Postgres (`refunds.test.ts`, `parse-refunds.test.ts`). The click-through of the web "Record refund" form (by anyone) remains unverified — the author's own report says the same. |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Amazon/Walmart tiered category fees | Yes | `fees.ts` `REFERRAL_SCHEDULES`; `fees.test.ts` tier-edge tests; independently re-derived against Amazon/Walmart's public rate description above |
| 1 Refunds recover referral fee | Yes | `feeRecoveredCents`; `fees.test.ts` "refunds return the referral fee less the admin fee" |
| 1 Shopify sales tax excluded from revenue | Yes | `service.ts` `taxInclusive`; `fees.test.ts` "detects Shopify tax-inclusive totals only" |
| 1 TikTok rate verified, source cited | Yes | `fees.ts` header cites the two knowledge-base URLs; independently re-verified 6% + 20%/$5 cap via WebSearch |
| 2 Shopify refunds pulled from order | Yes | `integrations/channels/shopify/refunds.ts`; `src/integrations/channels/shopify` suite green (code-reviewed, not live-clicked — see above) |
| 2 CSV refund columns / manual record | Yes | `csv/parse.ts` (`ParsedCsv.refunds`), `recordRefund`; `parse-refunds.test.ts` green |
| 2 Refunds reduce profit on their date | Yes | `refund_events.refundedAt` read by `refundGroups`/`mergeRefunds` in `getProfit`, and by `orderProfit`; day-view `GROUP BY 1` fix covered by `refunds.test.ts` |
| 3 Money in integer cents + property tests | Yes | `fees.test.ts` "fee math properties" — 3 seeded 2000-run property checks, all integer-cents assertions |
| 4 UI: refunds/fees separate lines | Partially | Code read confirms Refunds column + total card + "Record refund" form (en/es); build and unit tests pass. Not clicked through in a browser by me (infra outage) or by the author (report says so) — this remains unverified end-to-end |

## Blocking findings
1. `invai-backend/src/modules/finance/refunds.ts:127` (`recordRefund`) and `invai-web/src/features/finance/order-profit.tsx` (the "Record refund" form) — a manual refund is validated only for `amountCents > 0`. Nothing checks it against the order's (or order item's) sale total, or against refunds already recorded on that order/item, and `finance.refunds` has no `update`/`delete` procedure to fix a mistake (`invai-contracts/src/contract/finance.ts:80` only exposes `record`/`list`). Failure scenario: an office user types $999.00 instead of $99.00 on a $60 CSV order with no refund column; the row is written as 99900¢, `getProfit`/`orderProfit` show a large permanent negative net for that period, and there is no way to correct it except a direct DB edit. This is money-correctness territory (AC3) and was explicitly in this round's scope ("a refund can't exceed the order total, or if it can, that's handled") — right now it is neither prevented nor handled. Fix: reject (or clamp, with a clear signal) an `amountCents` that would push the order/item's cumulative refunds past its sale total, or at minimum cap the single-call amount at the order's `buyerTotalCents`.

## Checks
- [x] Only owned paths changed (`git diff --stat`) — plus the two pre-approved grant hunks named in the prompt
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened (scan-test-weakening: no hits in either repo, scoped to this commit)
- [x] Tenancy (`refund_events` has `tenantPolicy`; both `ingestChannelRefunds` call sites in `channels/sync.ts` run inside `withTenant`; router uses `withTenant` throughout), idempotency (`ingestChannelRefunds` upserts on `(companyId, channel, channelRefundId)`, keeps first `refundedAt`, re-sync verified by `refunds.test.ts`), money in cents (all `*Cents` integers, property-tested), en/es text (both `i18n/en.ts` and `i18n/es.ts` gained the same 4 lines) — all good **except** the refund-amount bound above
- [x] Decisions recorded where needed — the two granted out-of-scope hunks (`channels/sync.ts`, `integrations/channels/types.ts`) were pre-approved by the tech lead per this round's prompt; no new decision doc needed for a hunk this small

## Optional notes (not blocking)
- Contracts `CHANNEL_RULES.tiktok.transactionPct` is still 8 (should be 6, per the architect's note in `wave.md`) and the Amazon/Walmart free-text notes are stale too — the author correctly left these alone (outside the `RefundEvent`-only grant) and flagged it; someone still needs to take this fix.
- Walmart's "returned in full, no admin fee" refund assumption is honestly flagged in `fees.ts` and the report as unverified against the Retailer Agreement — worth a pilot check, not a blocker.
- Two pre-existing failures unrelated to this card surfaced during the full suite run: `shipping/export-tracking.test.ts` (T-7-1) and a flaky `tenancy/invites.test.ts` — flagging for cross-card visibility, not this review's problem to fix.
