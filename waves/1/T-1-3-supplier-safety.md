# T-1-3: Tenants never order on InvAI's supplier account, and POs are crash-safe

| Field | Value |
|---|---|
| Wave | 1 |
| Scope ref | always-in-scope: security (money); `product/scope.md#mvp-in` item 6 |
| Backlog | B-55, B-64 |
| Owner | integrations-engineer (with inventory module paths granted on this card) |
| Reviewer | reviewer |
| Co-reviewers | security-reviewer, backend-foundation (migration), backend-engineer (inventory), architect (the `ReceiveInput.idempotencyKey` contract addition) |
| Risk flags | payments, migration |
| Model | opus |

## Owned paths (edit)
- `invai-backend/src/integrations/suppliers/**`
- `invai-backend/src/modules/inventory/**`
- `invai-backend/src/db/schema/inventory.ts` and its generated migration
- tests next to these files

## Evidence
`build/audit-2026-09-24.md` §A-BE B-55 and B-64.

## Acceptance criteria
1. `getSupplierAdapter` never falls back to the platform's S&S env keys for a tenant:
   - no tenant credentials → mock in dev/test, and a clear "connect your supplier account" error in production;
   - `listSuppliers` reports `live` only when the tenant's own credentials exist.
2. `submitPo` is crash-safe:
   - it records an idempotency key and a `submitting` state in the DB first;
   - it calls the supplier **outside** the transaction, passing the idempotency key (or PO number) the supplier dedupes on;
   - it then records the supplier order id.
   A retry after a crash reads back first and never orders twice (a test simulates a commit failure after the supplier accepted).
   - Note: today `modules/inventory/router.ts` opens one `withTenant` transaction around the whole `submitPo` call, and `submitPo` calls `adapter.placeOrder` mid-transaction while holding the PO's `FOR UPDATE` lock. To get a real gap between "mark submitting" and "call the supplier," `submitPo`'s signature has to change so it opens its own short transactions (mark submitting → commit → call supplier → mark submitted/failed → commit) instead of receiving one pre-opened `tx` from the router. Change the router call site to match. `po.poNo` is already unique per company and stable, so it can be the idempotency key with no contract change.
3. `receivePo` is idempotent: the same receipt submitted twice counts once (a client key, or a receipt id). This needs a new optional, additive field on the contract's `ReceiveInput` (e.g. `idempotencyKey`), since a resubmit of identical quantities can also be a legitimate second delivery, not just a retry. `invai-contracts/**` is architect-owned; see wave.md's "Agreed interfaces" for the stub the architect commits first.
4. `cancelPo` on a submitted PO cancels at the supplier when the adapter supports it. Otherwise it refuses, with a message telling the user to cancel with the supplier first.
5. Existing inventory tests pass. New tests cover 1–4.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test` in invai-backend, with your own test DB.
- In a script or curl against your own API port, as `owner@desertbloom.test`: submit a PO twice, receive twice, and show a single supplier order and correct stock.

## Out of scope
- UI for supplier settings (B-86, wave 6).
