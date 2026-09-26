# 0013: Remove `production.scanBatch`

- Status: accepted (2026-09-26), T-13-3 (B-104), plan review r1 by product-manager + architect
- Type: contract

## Context
Audit A-FE found 13 contract procedures with no UI caller. The wave 13 plan review (product-manager
+ architect, r1) checked each one against the screens/flows it should back: 12 of 13 are the missing
half of an already-shipped screen (e.g. `inventory.purchaseOrders.create/update` backs the PO list at
`inventory/purchase-orders.index.tsx:81`) and stay, to be wired up as follow-up work (backlog B-112).

`production.scanBatch` (`invai-contracts/src/contract/production.ts`, `auth: "floor"`) is different: it
has never had a caller. It was added in the very first v1 contract commit (`34eabe4`) alongside
`production.scan`, but `invai-floor/src/api/rpc.ts` has only ever called `production.scan` — checked
against the full history of that file (`git log --all -p -- src/api/rpc.ts` and `git log --all
-S"scanBatch"`), not just its current contents. The floor replays queued offline scans one at a time
through `production.scan` (each commits on its own, so one bad scan can't undo the others); nothing in
web, the vendor portal, or any test suite references it either.

## Decision
Remove `production.scanBatch` now, via `contract-deprecation`, rather than expand-then-wait:

1. **Find every use** (skill step 2): `grep -rn "scanBatch" invai-backend/src invai-web/src
   invai-floor/src invai-ui/src` — only the contracts procedure definition and the backend router
   handler that mechanically delegates to `svc.scan`. No consumer, no test, no floor outbox entry ever
   shaped for it.
2. **Skip the wait-out (skill step 6, ADR 0012 rule 5 exception).** ADR 0012's 14-day grace window and
   `FLOOR_COMPAT_BASELINE` hold exist to protect a tablet that might still be running a build that sends
   the old shape, or that has old-shaped entries queued in its offline outbox. Both are checked against
   the real history above and neither has ever existed for `scanBatch`: no floor build, current or past,
   has ever sent it, so there is no old client to break and nothing queued to replay. `FLOOR_COMPAT_BASELINE`
   stays at its current value — no floor-facing shape actually breaks, because nothing floor-facing ever
   used this shape.
3. **Remove in this release.** `invai-contracts/src/contract/production.ts` drops the `scanBatch`
   procedure; `invai-backend/src/modules/production/router.ts` drops its handler. Contracts bumps its
   minor version (0.x rule) with a `CHANGELOG.md` line.
4. Not partner-facing (no vendor portal or public API caller), so `escalate-to-owner` doesn't apply.

## Consequences
- `POST /scans/batch` (`production.scanBatch`) no longer exists. Any out-of-tree or manual caller (none
  found) would get a 404 from oRPC's router, not a deprecation warning — acceptable given zero traffic.
- `production.scan` remains the only scan endpoint; the floor's one-at-a-time outbox replay is unchanged.
- The other 12 no-UI procedures from A-FE are intentionally kept; see `invai-docs/waves/13/wave.md`
  ("T-13-3: unused procedures") for the full per-procedure verdict table.
