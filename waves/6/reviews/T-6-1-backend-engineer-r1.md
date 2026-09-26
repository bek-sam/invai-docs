# Review of T-6-1 (round 1)

- Reviewer: backend-engineer (inventory) on Sonnet 5
- Author: web-engineer (+ backend-engineer inventory) on sonnet
- Verdict: approve

## Evidence I re-ran
Co-review scoped to the domain risk: `invai-contracts` `acbd294`/`57023f2` and `invai-backend`
`55ea446`, read against `modules/inventory/**` conventions (tenancy, idempotency, jobs, money) this
role owns. UI-side and design/UX evidence are covered by the other two files.

| Command | Result |
|---|---|
| `invai-contracts` (review worktree at `57023f2`): `tsc --noEmit`, `biome check .`, `vitest run` | pass / pass / 31 tests passed |
| `invai-backend` (review worktree at `55ea446`, own `.env`, own test DB `invai_test_t61_r1` created via `createdb -T invai`, migrated): `tsc --noEmit` | pass |
| `invai-backend`: `biome check .` | pass, no fixes |
| `invai-backend`: `vitest run src/modules/inventory` | 7 files, 47 tests passed |
| `invai-backend`: `vitest run` (whole repo, to check for cross-module regressions) | 71 files, 498 tests passed |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend-t61-review 55ea446~1` | 2 hits, read below |
| New tests (`mark-placed.test.ts`, `jobs.test.ts`) copied onto `55ea446~1` and run there | all 6 fail (`markPlacedPo is not a function`) — the tests are real, not tautological |
| Real API pass on DB copy `invai_t61_r1_copy` (API :3191, `REDIS_URL` `/9`): draft PO → mark-placed → idempotent retry → 409 on a different ref on a non-draft PO; double-submit receive; a cycle count; a supplier API key round-trip | see criteria table; DB checked directly via `psql` |

## Acceptance criteria (backend slice)
| # | Met? | Evidence |
|---|---|---|
| 2. `markPlaced`: draft-only, idempotent, `INVALID_TRANSITION` otherwise | yes | `markPlacedPo` (`service.ts`) is a pure state transition inside the caller's `withTenant` transaction: same-ref retry on an already-`submitted` PO returns the current row unchanged (checked by identity, `po.status === "submitted" && po.supplierOrderId === input.supplierOrderRef`); anything else non-draft throws `invalidTransition(...)`. Confirmed live: `CALL-9981` twice → same row both times; `CALL-DIFFERENT` on the now-submitted PO → `409 {code:"INVALID_TRANSITION", data:{from:"submitted",to:"submitted"}}`. An `outbox` event (`po.submitted`) and an audit entry are recorded — consistent with how the rest of this module emits state-change side effects. |
| 3a. `submitting` no longer masked as `draft` | yes | `toPurchaseOrders` now returns `r.status` as-is; `listPos`'s `draft`-filter fold into `submitting` was removed since the real status is exposed directly. `po-safety.test.ts` was updated (not weakened — see below) to assert `submitting`, and I re-ran the whole file plus the rest of the module suite; nothing else depended on the old masking behavior. |
| 3b. Stuck-`submitting` alert, 5-min sweep, >15 min | yes | `stuckSubmittingPos` (query, `lt(submitAttemptedAt, now - 15m)`) is swept by `stuckSubmittingPoJob` every 5 minutes (`STUCK_SUBMITTING_SWEEP_EVERY_MS`), fanned out per-shop by `stuckSubmittingSweepJob` via `withSystem` (cross-tenant, ids only — appropriately narrow use of `withSystem`, matches the codebase convention of using it only for cross-tenant/system jobs), and each company's sweep runs inside `withTenant`. The alert reuses `sync_broken` with a clear comment explaining why (no dedicated kind exists yet, same precedent as shipping's stuck-intent sweep) and dedupes per PO via `dedupeKey`. Tested with a backdated fixture (`jobs.test.ts`), not a live wait — exactly what the card required; I additionally confirmed a PO backdated only 5 minutes does *not* alert (the "still inside the in-flight window" test), which is the right boundary check. |
| — `blankLabels` (T-6-2 dependency) | yes, as documented | Validates the variants belong to the caller's tenant before rendering, calls the (not-yet-implemented) imaging `/labels/qr` endpoint, and correctly reports `notFound` if none of the requested variant ids resolve. The report is upfront that the imaging endpoint doesn't exist yet — that's shared, tracked scope under T-6-2's co-review, not a gap in this card's own code. |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed: contract diff touches only `inventory.ts`/`schemas/inventory.ts` (isolated per-commit from the other cards' stubs that happen to sit in the same shared repo history); backend diff touches only `src/modules/inventory/{jobs,router,service}.ts` and their tests.
- [x] Nothing outside scope.
- [x] Tests exercise the behavior, none weakened: scan flagged (a) the `draft`→`submitting` assertion swap in `po-safety.test.ts` — read the diff, it's checking the new correct value, not loosening anything (still a `toBe(...)` on a fully-qualified status, no loss of strength); (b) `if (!env.isTest)` guarding the scheduler registration in `jobs.ts` — this is the exact same idiom already used in `channels/billing/finance/shipping/orders/today` jobs files (grepped), so it's a pre-existing, repo-wide convention to keep test runs from registering real cron schedulers, not a T-6-1-specific way to dodge coverage. The job's actual *logic* (`stuckSubmittingPoJob`) is fully covered by `jobs.test.ts` via `runJobInline`, bypassing only the scheduler registration, not the behavior.
- [x] Tenancy: every read/write in the new code runs inside `withTenant`; the only `withSystem` use (fan-out across companies in `stuckSubmittingSweepJob`) is narrowly scoped to selecting company ids and carries an explicit comment justifying it, matching the "cross-tenant jobs" carve-out in `CLAUDE.md`.
- [x] Idempotency: `markPlaced` (state-transition, naturally idempotent) and `receive` (client `idempotencyKey`, unique on `purchase_order_receipts.idempotency_key`) both verified with a live double-call producing exactly one effect (checked `inventory_movements`/`purchase_order_receipts` row counts directly in Postgres, not just the HTTP response).
- [x] Money in cents: `subtotal`/`total`/`unitCost` all integer cents throughout the manual-PO and count flows (`639`, `15975`, etc. — no floats anywhere in the diff).
- [x] Decisions recorded where needed: none required (additive contract change, no deprecation).

## Optional notes (not blocking)
- `blankLabels` calls an imaging endpoint that doesn't exist yet; this is called out plainly in the report and is fine to land now since T-6-2 depends on the same procedure existing, but the tech lead should make sure the imaging co-review (under T-6-2) actually lands `/labels/qr` before this path is exercised for real (it will currently fail with an `upstream` error against a live imaging service until that ships).
- Confirmed (mine and the primary reviewer's worktree setup) that the shared repos' `node_modules/@invai/contracts` symlinks were briefly re-pointed during isolated per-commit testing and have been restored to `../../../invai-contracts`; no `pnpm install` was run in any worktree, only `node_modules/.bin/*` directly.
