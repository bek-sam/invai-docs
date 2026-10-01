# Review of T-P6-4 (round 1)

- Reviewer: reviewer on opus. Author: backend-foundation on opus. Commit invai-backend 8de1b64 (on 5557014), worktree under /tmp.
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `tsc --noEmit`; `biome check .` (worktree at 8de1b64) | exit 0; 463 files, no fixes |
| `REDIS_URL=…/7 vitest run src/db/seed --reporter=dot` | 6 files, 14 passed |
| `scan-test-weakening.sh <wt> 5557014`; `git diff --name-only 5557014 8de1b64` | no hits; only `src/db/seed/{builder,index,plan-order,plan-order.test}.ts` |
| Seed 8de1b64 on fresh `invai_p6_r4a`, then `_r4b` (imaging on :8041, Redis /7, own output file) | exit 0, 54 s and 50 s |
| 19-line fingerprint SQL on A vs B (orders/items by state, reprint set md5 by order_no:line:unit, reprints rows, all-items md5, transitions, sheets/transfers, scans, shipments/labels, profit_lines, QA, alerts, users+pins+stations, stock md5, delivered-before-ready) | identical except open-order md5 that includes exact `ship_by` timestamps (now-relative); same md5 by order_no+status+ship-by date |
| Base 5557014 seeded on `invai_p6_r4c` at the same hour, same SQL | orders by status, users/pins/stations, alerts, QA identical; items 6401→6398 (ready 46→39, pressed 15→19, shipped 690→692), transfers 584→589, scans 236→242, delivered_before_ready 219→0 |
| Worker on `_r4b`: pool (ready, no transfer, QA not failed) at seed exit, after outbox drain, after 2 min | 39 (md5 da8c…) → 39 same md5, QA passed=40 both → 42 after `channels.poll` imported mock Shopify #3001, #3002 |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | Report names 7 causes with file:line; each matches a hunk in the diff (plan sort, reprint pick, history scan pick, vendor, at-risk alerts, blanks order, timeline tie-break) |
| 2 | yes | A vs B identical above; reprint set 168 items, same md5 on both |
| 3 | yes | Open orders 88, same status counts as base; open-order numbers differ from base because numbering follows plan order (base itself moves with time of day); E2E uses CSV orders 3310000001/2 and dynamic lookups only |
| 4 | yes (with the author's out-of-seed finding) | Drain doesn't move the pool (same md5); the mover is the worker's mock poll, reproduced (39→42). Step-5 ≥ 80% left to the gate, as the report says |
| 5 | yes | 50–54 s vs base 50 s; T-P6-1 guard untouched (index.ts +2 lines). Imaging-down run not re-run (author: exit 0) |
| 6 | partly, justified | `runDesignQa` inline via `settleQa`; R2 mechanism not reproduced (QA passed=40 before/after drain), as reported |
| 7 | yes | plan-order.test.ts (3 tests) for the new helper |

## Blocking findings
none

## Checks
- [x] Only owned paths changed  - [x] Nothing outside scope (no product code; `settleQa` only calls the existing `runDesignQa`)
- [x] Tests not weakened  - [x] Tenancy/idempotency unchanged (seed only)  - [x] No decision needed; 0020 mix kept: 168 reprints = 2.9% of 5874 pressed+, 164/168 partial

## Optional notes (not blocking)
1. builder.ts:573-595: with imaging down, `settleQa` leaves designs `pending` instead of the old stand-in `passed` (report says "as before"). Pool unaffected (only `failed` excluded, sheets.ts:173).
2. Remaining time-dependence: profit_lines cutoff (report gap 1) and the poll (gap 2); suggest a gate card for gap 2.
3. Cleanup: DBs a/b/c dropped, worktrees removed, imaging and worker stopped, Redis /7 flushed (my slot; it held 964 keys incl. stale market jobs from earlier runs).
