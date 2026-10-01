# Review of T-P4-1 (round 1)

- Reviewer: reviewer on Fable 5.1
- Author: backend-engineer on Opus 5.5 (invai-backend `8d69b64`); metrics SQL by data-analyst (invai-docs `8881d5a`)
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck && pnpm lint` (invai-backend HEAD) | pass; biome 457 files, no fixes |
| `pnpm vitest run src/modules/finance src/modules/orders/import-edits.test.ts import.test.ts import-cancel.test.ts src/modules/digest/digest.test.ts src/db/rls-coverage.test.ts src/api/authz.test.ts` | 11 files, 88 passed |
| `pnpm vitest run src/modules/analytics src/modules/market src/modules/ai` | 18 files passed, 270 tests; 1 failed = `market.acceptance.test.ts:689` AC17 (QA sibling-row fixture, T-P4-5, expected); 1 pre-existing skip. `finance-parity.test.ts` green against the fixed metrics SQL |
| Base proof: worktree at `e3c3cf7` + HEAD's `reprint.test.ts`, `import-edits.test.ts`, `refunds.test.ts` | 6 failed / 17 passed: AC1 (`3000 != 5500`), AC2 (`2 != 1` losing), 3 re-import tests (`updated:1`, reprinted unit stays `ready` on line-cancel), refund scope (resolved instead of rejecting). Worktree removed |
| `scan-test-weakening.sh invai-backend e3c3cf7` | 1 removed assertion = the `300+75 -> 300+150` replacement (verified below); `toBeDefined` hits are T-P4-4's ai tests; no skip/only/mocks/test-only branches |
| Live, scratch `pg_dump` copy of the dev DB, API :3141, Redis 14: owner `files.presignUpload` + `channels.importCsv` of `fixtures/etsy-sold-order-items.csv` (holds seed order 3310000001, line 2 qty 2 with unit 2.1 `ready:R`) sent twice | both `ordersUpdated:0, ordersSkipped:4`; order stays `item_count 3`, items `1.1:packed,2.1:ready:R,2.2:packed`; `order_items` total 6395 before and after (AC6) |
| Live `finance.orderProfit` on that order | revenue 7496, reprinted line 2498 `isReprint:true`, 3 lines |
| Live `presser@` -> `analytics.losingOrders` | 403 `FORBIDDEN` (`finance.read`) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `reprint.test.ts` AC1: revenue 5500 = plain twin, reprinted line 2750, 2 lines, fees/blank equal, transfer +300, net −300; red on base. `service.ts:605-609` sellable = all items |
| 2 | yes | AC2: costly order listed with `units 2, revenue 5500, cm2<0`; cheap reprinted order not listed; red on base |
| 3 | yes | 3 re-import tests (`import-edits.test.ts:443-510`) green at HEAD, red on base; `import.ts:528-534,681-685,860-863` filters gone; no other `isReprint` read left in `orders/` |
| 4 | yes | leakage `300+150`: same formula `blank + transfer/(1+reprints)`, item now holds both transfers (REG.transfer*2=300, /2=150); old 75 was the sibling artifact. digest AC10 keeps `revenue 2500` / `net` assertions. testkit line = same item flagged + 2 transfers |
| 5 | yes | no new `withSystem`; all SQL keeps `company_id = ctx.companyId`; rls-coverage + authz green; AC2 cross-tenant `NOT_FOUND` |
| 6 | yes | live double import above (scratch copy, shared dev DB untouched) |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (14 backend files in finance/orders/analytics/market/digest; docs commit only `metrics/sql` + matching `metrics/definitions`, by the path owner)
- [x] Nothing outside scope (remaining `isReprint` reads: production writers, seed, finance flag copy-through, `ledger.ts:195` loads it but never branches on it, `orders/service.ts:278` contract mapping)
- [x] Tests exercise the behavior, none weakened
- [x] Tenancy, idempotency (recompute run-twice `toEqual`; import sent twice = no-op), money in cents, no copy changes
- [x] Decision 0020 recorded and referenced in code comments

## Optional notes (not blocking)
- `inventory/ledger.ts:187,195` and `market/service.test.ts:402` keep an unused `isReprint` field/option; harmless.
- `8881d5a` also edited three `metrics/definitions/*.md` beyond the grant's "SQL only" wording; they are the path owner's own files and now match the SQL.
- QA's uncommitted edits to `market/*.acceptance.test.ts` appeared in the shared tree after my test runs; excluded from this verdict.
- Release note (ruling 3) is in the author's report; profit lines older than the nightly window keep $0 until `finance.recompute`.
