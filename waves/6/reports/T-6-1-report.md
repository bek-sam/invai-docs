# T-6-1: Inventory UI — report

## Summary
Built manual PO create/edit, "mark placed by phone/email" for suppliers with no
ordering API (B-86), receive-form idempotency, the real `submitting` PO status,
a 15-minute stuck-submit alert, a stock cycle-count screen, and the inventory
& supplier settings page. Added the `inventory.blankLabels` procedure T-6-2
depends on.

## Commits
- `invai-contracts` `acbd294` — `purchaseOrders.markPlaced` + `inventory.blankLabels` stubs (wave.md verbatim).
- `invai-contracts` `57023f2` — missing `CountResult`/`SupplierInfo` TS type exports (needed by the web UI).
- `invai-backend` `55ea446` — `markPlacedPo`, real `submitting` status, stuck-submitting alert sweep, `blankLabels` service.
- `invai-web` `13927c3` — PO create/edit dialog, mark-placed dialog, receive `idempotencyKey`, stock Count tab, `settings/inventory` route, nav entry, en/es keys.

## Note on the architect's stub commit
The prompt said to poll `invai-contracts` until the architect's wave-6 stub
commit landed, but `wave.md` says stubs are written there for each card owner
to implement verbatim — not committed by the architect. I polled ~90s, saw no
wave-6 commit and no `markPlaced`/`blankLabels` in the contract, and proceeded
to add them myself per `wave.md`, tagged with a clear commit message. Shortly
after, the architect *did* start landing other cards' stubs directly into the
shared `invai-contracts` checkout (T-6-5's `printsInHouse`, T-6-2's bin/sheet
stubs) — confirming stubs land incrementally, per-card, not as one wave-6
commit. My `markPlaced`/`blankLabels` commit was not disturbed by this.

## Acceptance criteria
1. **Manual PO** — `PoFormDialog` (create + edit-while-draft) with supplier
   select, `BlankPicker`-driven lines (qty, unit cost), freight, notes.
2. **Mark placed manually** — `purchaseOrders.markPlaced({ id, supplierOrderRef })`,
   draft → submitted, idempotent on repeat with the same ref (`INVALID_TRANSITION`
   otherwise). UI: "Mark placed by phone/email" button + dialog on the PO page.
3. **Receiving** — receive form sends a per-receipt `idempotencyKey`
   (`crypto.randomUUID()`, refreshed after each successful receive so a retry of
   the *same* submission reuses it). PO list/detail show `submitting` (backend no
   longer masks it as `draft`). Stuck-submit alert: `inventory.jobs`'
   `stuckSubmittingPoJob`, a 5-minute sweep per company, raises a `sync_broken`
   alert (closest existing kind — no dedicated kind added, same precedent as
   shipping's stuck-intent sweep) after 15 minutes in `submitting`. Tested with
   a backdated `submitAttemptedAt` fixture, not a live wait.
4. **Stock count** — new "Count" tab on `/inventory/stock`: pick a location,
   add blanks via `BlankPicker`, live expected-vs-counted diff per line, submit
   through `inventory.count`, last-count variance summary shown after.
5. **Settings** — `/settings/inventory`: per-supplier account number,
   free-freight threshold, and API key (masked "set" indicator from
   `suppliers.list().hasApiKey`, since `apiKey` is write-only; type-to-replace or
   remove-to-clear), plus velocity window / lead days / safety days /
   reserveOnImport.
6. **Quality** — en/es keys added by hand; existing shared components
   (`BlankPicker`, `Field`, `NativeSelect`, dialogs) used throughout for
   consistent 390px/keyboard/loading-empty-error behavior; no new components
   introduced outside owned paths.

## Verify
- `invai-contracts`: `pnpm typecheck && pnpm lint` — pass.
- `invai-backend`: `pnpm typecheck && pnpm lint` — pass. `pnpm test` (inventory
  module, `invai_test_t61`): 47/47 pass, incl. new `mark-placed.test.ts` and
  `jobs.test.ts` (stuck-submit sweep with backdated fixture).
- `invai-web`: `pnpm typecheck && pnpm lint && pnpm test` — pass (76/76).
  `pnpm build` succeeds (routeTree.gen.ts regenerated for `/settings/inventory`).
- Browser pass on DB copy `invai_t61_copy` (API :3110, web :5113, Redis /1):
  created a manual "Other"-supplier PO, marked it placed (draft → submitted,
  `CALL-9981`), fast double-clicked "Receive 25 units" (received exactly 25,
  not 50 — idempotency held), ran a cycle count on the same blank (68 → 65,
  diff −3, submitted), and saved inventory settings. 4 screenshots saved.

## Known gaps / follow-ups
- `blankLabels`' imaging call (`POST /labels/qr` on invai-imaging) doesn't
  exist yet — that endpoint is shared with T-6-2's bin labels and flagged in
  `wave.md` for imaging-engineer co-review under T-6-2. My service function
  calls the documented shape; it will start working once that endpoint lands.
- PO create/edit dialog has no location picker (defaults server-side to the
  default location) — kept out of scope given no multi-location need surfaced
  in the AC text.
- Cleanup done: `invai_test_t61` and `invai_t61_copy` dropped, Redis db 1
  flushed, API (:3110) and web (:5113) processes killed.
