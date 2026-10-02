---
name: tx-split-explicit-companyid-pattern
description: When a card takes an external call (imaging, carrier, etc.) out of an open DB transaction, check tenant context is threaded via an explicit companyId parameter, not an ambient tx — and that any natural-key guard (file_key) is a race guard, not a tenant guard.
metadata:
  type: project
---

T-P2-2 (2026-09-30, catalog `renderDesignPreviews`) split one `withTenant(tx => …)` transaction
that held a DB connection across `imaging.preview()` HTTP calls into: a short read tx, the imaging
call with no tx open, then a short per-file write tx guarded on `file_key` still matching. The
function signature changed from `(tx, ctx, id)` to `(companyId, ctx, id, opts)` — it no longer
takes a `Tx` at all and opens its own `withTenant(companyId, …)` at each step.

**What to check on this shape of refactor:**
1. The `companyId` used at every step (read, external call's `isCompanyKey` check, write) must be
   the same explicit parameter, not `ctx.companyId` in one place and the parameter in another —
   even if they happen to be equal today, that's a trap for the next caller who builds a `ctx` for
   a different tenant than the `companyId` argument.
2. Confirm the function's new callers pass a `companyId` that still originates from a trusted
   source (a job's queued input set at enqueue time inside the original tenant's `withTenant`),
   not from any request-controlled field.
3. A `WHERE id = ? AND naturalKey = ?` write guard added to stop a stale write after a
   concurrent replace (good practice, see [[imaging-key-trust-model]]) is **not** a tenant
   boundary by itself — it has no `company_id` in it. The thing that actually stops a
   cross-tenant write is still RLS, because the write runs inside `withTenant(companyId, …)`.
   If a future diff ever moves this kind of write to `withSystem` "for performance," the natural-
   key guard alone would not catch a cross-tenant row match — block on that.

**How to apply:** for any `files`/`tenancy`-flagged card that removes a transaction wrapper
around an external call, re-run the existing cross-tenant NOT_FOUND tests (they should still pass
unchanged — if the author had to edit them to keep them green, read why) and diff the
`isCompanyKey` call sites to confirm they still fire before every call to the external client, not
just the first one in a loop.
