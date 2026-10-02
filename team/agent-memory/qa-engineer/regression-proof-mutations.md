---
name: regression-proof-mutations
description: How to prove an idempotency acceptance test catches a regression (worktree mutations), and the traps hit on T-20-3 (gate deadlocks, layered read-backs, per-run unique shop ids, guard blocking git checkout in a worktree)
metadata:
  type: feedback
---

Prove each side-effect test red by removing one guard in a detached worktree (`git worktree add --detach ../invai-backend-<card> HEAD`, symlink `node_modules`, copy `.env` and your test files), run the file, then restore with `git show HEAD:<path> > <path>`.

**Why:** the card (T-20-3, 2026-09-28) requires "fails when the guard is removed, passes on main"; a test that passes on mutated code proves nothing. `guard-bash.py` blocks `git checkout --` even inside your own worktree, so `git show HEAD:` is the revert.

**How to apply:**
- A "second request while the provider call is open" test must let a *wrong* second provider call return at once (`if (calls !== 1) return;` in the fake's hook); otherwise a removed guard shows up as a 30 s timeout (gate deadlock), not a clean count assertion.
- A concurrent-double test with no gate often passes even with the guard removed, because the fake's call completes before the loser reads back; hold the first call open to prove the guard.
- Read-backs can be layered (Shopify: fulfillment-order `CLOSED` status *and* `remainingQuantity`); mutate the branch that decides "nothing left → done" rather than one filter.
- `channel_connections` has a cross-tenant unique `(channel, external_shop_id)`: any fixed `externalShopId` breaks the second run on the same DB. Use a per-run suffix.
- Shopify's orders query sends `after: null` on page one (not undefined).
- T-P4-5 round 2 (2026-10-01): `git worktree add ... HEAD` snapshots the last **commit**, not your
  uncommitted edits in the main tree. If the new assertion lives in an uncommitted test file, copy
  that file into the worktree too (`cp <repo>/<test> <worktree>/<same path>`) before mutating
  product code and running the probe — otherwise the worktree still has the *old* test, the probe
  silently passes on reverted product code, and you wrongly conclude the new assertion is red.
