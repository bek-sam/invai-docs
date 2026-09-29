# Wave 22 plan review — architect

**Verdict: approve with changes**

## Checked
- Ownership table vs. actual card "Owned paths": T-22-1 (contracts only) and T-22-3 (integrations +
  a named grant into `shipping/{router,service}.ts`) don't collide with anything else. Concurs with
  PM's required fix (drop scope item 4, add item 8 to T-22-1's scope ref).
- Contract-first order is right: T-22-1 lands day 1 with additive stubs (`NOT_IMPLEMENTED` via
  `stubRouter()`), T-22-2 runs in parallel (no contract dependency), T-22-3/4/5 start after T-22-1.
- Confirmed against `invai-contracts/src` that every T-22-1 addition is genuinely new and additive:
  no `scanForms`/`verifyAddress` namespace, no `Rate.expiresAt` (shipping.ts already has a
  `RATE_EXPIRED` 409 error on `shipping.buy` waiting for it), no `QC_FAIL_REASONS`, exist today.
  `production.ts`'s `qc` procedure already takes `reprintReason: REPRINT_REASONS` on fail — see A2.
- Composite-FK retrofit is architecturally sound and correctly scoped: checked
  `invai-backend/src/db/schema/vendors.ts` — `vendorConnections.vendorCompanyId` and
  `vendorAccess.vendorCompanyId` reference `companies.id` (not another tenant table), so they're
  correctly excluded by AC1's "FK from a tenant table to another tenant table" wording. Since `id`
  is already a global unique PK, the new `(company_id, id)` unique index is trivially satisfiable;
  since the app already loads parents under `withTenant` before insert (the documented pattern for
  today's single-column FKs), existing dev/seed rows should already satisfy the composite
  constraint — but see A6 for the contingency if `VALIDATE` finds one that doesn't.

## Required changes
1. **T-22-2 and T-22-4/T-22-5 share the same schema files; the plan only sequences their
   migrations, not the edits themselves.** The ownership table has T-22-2 owning
   `src/db/schema/*.ts` "FK constraints and indexes only" while T-22-4 owns
   `src/db/schema/{production,inventory}.ts` "new columns" and T-22-5 owns
   `src/db/schema/{orders,vendors}.ts` "new columns" — literally the same files, split by hunk.
   "Order and ownership" item 3 only says the *migration* order is T-22-2 → T-22-4 → T-22-5 ("the
   later card regenerates on a journal collision"); it doesn't say T-22-4/T-22-5 must wait for
   T-22-2's schema edits to be **committed** before they start editing `production.ts`,
   `inventory.ts`, `orders.ts` or `vendors.ts`. If T-22-2 is still mid-edit on `production.ts` when
   T-22-4 starts adding columns to the same file (both are "at most 3 builders at once" candidates
   after T-22-1 lands), that's a real concurrent-edit collision in a shared tree, not just a journal
   collision. State explicitly: T-22-4 and T-22-5 don't touch `src/db/schema/{production,inventory,
   orders,vendors}.ts` until T-22-2's schema commit lands (not merely until they generate their own
   migration).
2. **`QC_FAIL_REASONS` vs. the existing `reprintReason` on `qc` is ambiguous.** AC2 says "reuse
   existing reprint reasons where they match; list the mapping" and "`qcFail({... reason})` accepts
   it" — but `invai-contracts/src/contract/production.ts` already has one `qc` procedure taking
   `QcInput { result: pass|fail, reprintReason }`. Write the card so it's unambiguous whether this
   extends `QcInput`'s existing field (add `QC_FAIL_REASONS`, keep one `qc` procedure) or adds a
   second procedure name (`qcFail`) alongside it — the latter would duplicate `qc` with
   `result: "fail"` and violate "reuse an existing permission/procedure where the meaning matches."
   My read: extend `QcInput` (rename/add the reason field, produce `reprintReason` for the created
   `Reprint` from the mapping), no new procedure.
3. **Maintenance state has no owner among wave 22's cards.** `stations` (the table maintenance would
   naturally live on) is defined in `invai-backend/src/db/schema/tenancy.ts` and served by
   `src/modules/tenancy/router.ts` — not `src/db/schema/{production,inventory}.ts` /
   `src/modules/{production,inventory}/**`, which is all T-22-4 owns. Don't put
   `production.maintenance.start/end` state on the `stations` row (that needs an edit to
   `tenancy.ts`/`src/modules/tenancy/**`, which no wave-22 card owns or grants). Instead, model
   maintenance as its own production-owned table (e.g. `station_maintenance_events`, keyed by
   `stationId`, in `src/db/schema/production.ts`) — this also gives AC3's "start/end are idempotent
   and audited" a natural audit trail for free, entirely inside T-22-4's existing owned paths. State
   this explicitly in T-22-1 (so the contract's home for these procedures matches) and T-22-4.
4. **A scan must never throw for a business outcome; `STATION_BLOCKED_MAINTENANCE` as "an error
   code" contradicts that invariant.** T-22-1 AC2 calls it "a `STATION_BLOCKED_MAINTENANCE` error
   code," and `production.scan`'s own doc comment says exactly the opposite: "Never throws for a
   mismatch: `ok: false` with a `mismatch` reason is a normal result the tablet shows in red."
   `MISMATCH_REASONS` in `invai-contracts/src/schemas/production.ts` already has `item_on_hold`,
   `item_cancelled`, `wrong_station` for exactly this kind of blocked-scan case. Add
   `station_blocked_maintenance` to `MISMATCH_REASONS` (additive, appended at the end) and return it
   through `ScanResult.mismatch`/`nextAction`, not as a thrown `.errors()` code, for the `scan`
   procedure. A thrown error is fine for `maintenance.start/end` themselves (e.g. "already under
   maintenance"), just not for the scan path.
5. **Trigram indexes (AC5) can't use `CREATE INDEX CONCURRENTLY` inside `pnpm db:migrate` as it
   exists today.** Checked `invai-backend/src/db/migrate.ts`: `migrate()` (drizzle-orm) applies every
   pending migration inside one transaction, and Postgres refuses `CREATE INDEX CONCURRENTLY` inside
   a transaction block. No `drizzle/online/` runner exists yet (that's `zero-downtime-migration`'s
   proposed future path, not built). Since this is pre-launch with no live shop traffic yet, a plain
   (non-`CONCURRENTLY`) `CREATE INDEX` inside the normal migration is safe and appropriate here —
   say so explicitly in the card so the implementer doesn't reach for `CONCURRENTLY` and get a
   migration failure, and doesn't feel obligated to build the online-index runner as a prerequisite.
6. **State the contingency if `VALIDATE CONSTRAINT` fails on the seeded dev copy.** AC1 says the
   migration "runs... in < 60 s," which proves timing but not that every existing row already
   satisfies the new composite FK. Given 21 waves of multi-agent writes, it's plausible some row
   doesn't. Add one line: if `VALIDATE` finds a violation, that's a data-integrity bug to find and
   fix at its source (report it), not a constraint to weaken or a row to silently delete.

## Notes (non-blocking)
- Agree with PM's required scope-ref fix on T-22-1 (drop item 4, add item 8).
- T-22-5's grant into `src/modules/ai/service.ts` for listing-attributes mapping, reviewed by
  ai-engineer, matches the existing pattern from wave 18/19 (memory: the assistant's `tool_result`
  yield lives in that file; any touch needs the ai-engineer in the loop) — correctly done here.
