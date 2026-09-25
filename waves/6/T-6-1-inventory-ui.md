# T-6-1: Inventory UI
Scope: item 6. Backlog: B-86, plus follow-ups (the "mark placed manually" action, `idempotencyKey` on the receive form, `submitting` returned by the backend, alerting on a PO stuck in `submitting`).

## Owned paths
- web: the inventory routes and features, the inventory settings route, own i18n keys
- backend: `modules/inventory/**` (`markPlaced`, `submitting` status, the stuck-submit alert, and `inventory.blankLabels` — T-6-2 depends on this landing; see exact stub in `wave.md`)
- tests

## Acceptance criteria
1. **Manual PO:** create or edit a PO (supplier, lines with variant search, quantities, costs in cents). Editing is allowed only while it's a draft.
2. **Mark placed manually:** for suppliers with no API, via `inventory.purchaseOrders.markPlaced({ id, supplierOrderRef })` (exact stub in `wave.md`). Valid only from `draft`; sets `supplierOrderId`/`submittedAt` and moves to `submitted`. No client `idempotencyKey` — it's a pure state transition with no outbound call, so a same-ref retry on an already-submitted PO is a safe no-op; a different ref on a non-draft PO is `INVALID_TRANSITION`.
3. **Receiving:** the web receive form sends an `idempotencyKey`. The PO list shows the `submitting` state (the backend now returns it). A PO stuck in `submitting` for more than 15 minutes raises an alert — **test this with a backdated `submittedAt`/fixture timestamp**, not a live 15-minute wait in the browser pass.
4. **Stock count screen:** pick a location or bin, enter counts, preview the difference, and submit through `inventory.count`.
5. **Inventory and supplier settings:** the S&S account number and API key (stored encrypted, shown masked), free-freight threshold, velocity, lead and safety days, and `reserveOnImport`.
6. **Quality:** en and es, 390 px, keyboard accessible, and loading, empty and error states.

## Verify
Run tsc, lint, test and build. One browser pass on a DB copy: make a manual PO, mark it placed, receive it with a double submit, do a count, and save settings. At most 6 screenshots.
