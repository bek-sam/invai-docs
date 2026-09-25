# Wave 6: office web for inventory, production, profit and AI listings, plus demo safety

- Goal (user outcome):
  - The office can make and edit POs, count stock and set up supplier details.
  - Shops that print their own DTF can run sheets.
  - Reprints and bins are managed and labeled.
  - Profit includes ad spend and exports.
  - AI listings can be copied or exported for CSV channels.
  - Demo workspaces can never spend real money.
- Plan reviewed by: product-manager and architect (`reviews/plan-*-r1.md`)
- Rules: `team/agent-brief.md` (token budget, decision 0011). B-93 (accessibility) moves to wave 7.

## Cards
| Card | Owner | Co-reviewers | Risk flags | Model | Status |
|---|---|---|---|---|---|
| T-6-1 Inventory UI | web-engineer (+ backend-engineer inventory) | product-designer | ui | sonnet | planned |
| T-6-2 Production UI: in-house print, reprints, bins and labels | web-engineer (+ architect state, imaging for labels) | product-designer, architect | ui | sonnet | planned |
| T-6-3 Profit: ad spend, export, drill-down | web-engineer (+ backend-engineer finance) | product-designer, data-analyst | ui | sonnet | planned |
| T-6-4 AI listings: copy, export, publish status, credits + B-101 | ai-engineer + web-engineer | product-designer, compliance-officer | ai, marketplace-policy | sonnet | planned |
| T-6-5 Demo workspaces can't spend (B-109) | backend-foundation + integrations-engineer | security-reviewer | payments, tenancy | opus | planned |

3 builders at once: T-6-5, T-6-1 and T-6-2 first, then T-6-3 and T-6-4.

## Numbers
- Test DB `invai_test_t6<k>`.
- API port `31<k>0`, web `51<k>3`.
- `REDIS_URL` `/<k>`.
- DB copy `invai_t6<k>_copy`.

## Web file ownership
- T-6-1: `routes/_app/inventory/**`, `features/inventory/**`, the inventory settings route.
- T-6-2: `routes/_app/production/**`, `features/production/**`.
- T-6-3: `routes/_app/analytics/**`, `routes/_app/settings/costs.tsx`, `features/finance/**`.
- T-6-4: `routes/_app/listings/**`, `features/listings/**`, the credits section of `settings/billing.tsx`.
- i18n: each card adds its own keys by hand.

## Agreed interfaces (exact shapes by the plan review; the architect commits the stubs)
- `inventory.purchaseOrders.markPlaced({ id, supplierOrderRef })`: for suppliers with no API. No `idempotencyKey` — see the contract stub; it's a pure state transition with no outbound call, so it's naturally idempotent.
- `SHEET_TRANSITIONS` gains an in-house path, `ready → printing → printed`, when the company prints in-house (a company setting, `printsInHouse`, exposed via `me.updateOrg`/`Org` — **needs a grant, see clarifications below**).
- Bin and blank labels return an S3 **key** (this codebase's existing file-reference convention — resolve with `files.downloadUrl({ fileKey })`; there is no separate "file id"/files table), not a new concept: `production.bins.labels({ binIds })` and `inventory.blankLabels({ variantIds })` → `{ key: string }`. Rendering is a new imaging endpoint (Python has `qrcode`; Node has no QR library and imaging already composes QR labels for sheets in `compose.py`).
- `ai.listings.exportCsv({ draftIds, channel })` → `{ key: string }`, one CSV row per **variant** (not per draft), with real `catalog.variants.sku`.
- Two gaps the cards' one-liners don't cover, added here: `production.reprints.reasonsByWeek` (no by-week breakdown exists today) and `finance.exportCsv` for profit (no export endpoint exists today).

## Contract stubs (exact)

All additive (new procedures / new optional fields / one appended enum value); nothing existing renamed or removed, so no `contract-deprecation` process is triggered. Not committed to `invai-contracts` per this review's read-only instruction — written here for each card's owner to implement verbatim.

### 1. `inventory.purchaseOrders.markPlaced` (T-6-1)
```ts
// contract/inventory.ts, inside purchaseOrders router
markPlaced: proc("purchasing.manage")
  .route({ method: "POST", path: "/{id}/mark-placed" })
  .input(z.object({ id: Id, supplierOrderRef: z.string().min(1).max(120) }))
  .output(PurchaseOrder)
  .errors({
    INVALID_TRANSITION: { status: 409, message: "Only a draft PO can be marked placed" },
  }),
```
Valid only from `status: "draft"`. Sets `supplierOrderId = supplierOrderRef` (the field already exists on `PurchaseOrder`), `status: "submitted"`, `submittedAt: now()`. Idempotent by construction: a retry with the same `supplierOrderRef` on an already-`submitted` PO is a no-op that returns the current row; a different `supplierOrderRef` on a non-`draft` PO throws `INVALID_TRANSITION`.

### 2. `printsInHouse` company setting (T-6-2 — needs a grant, see below)
```ts
// schemas/tenancy.ts: Org gains
printsInHouse: z.boolean(),
// contract/tenancy.ts: me.updateOrg input gains
printsInHouse: z.boolean().optional(),
```
Backend: `CompanySettings` (`invai-backend/src/db/schema/tenancy.ts`) gains `printsInHouse?: boolean` — additive on the existing `settings` jsonb column, **no migration**. `modules/tenancy/service.ts`'s `toOrg()`/`updateOrg()` read/write it alongside `name`/`timezone`.

### 3. `SHEET_STATES` / `SHEET_TRANSITIONS` (states.ts) + two new sheet procedures (T-6-2 — needs a grant, see below)
```ts
export const SHEET_STATES = [
  "building", "ready", "printing", "sent", "acknowledged",
  "printed", "shipped", "received", "failed", "cancelled",
] as const;

export const SHEET_TRANSITIONS: Record<SheetState, readonly SheetState[]> = {
  building: ["ready", "failed", "cancelled"],
  ready: ["sent", "printing", "building", "cancelled"], // printing = in-house path
  printing: ["printed", "cancelled"],
  sent: ["acknowledged", "printed", "cancelled"],
  acknowledged: ["printed", "cancelled"],
  printed: ["shipped", "received"],
  shipped: ["received"],
  received: [],
  failed: ["building", "cancelled"],
  cancelled: [],
};

// contract/production.ts, inside sheets router
markPrinting: proc("production.build")
  .route({ method: "POST", path: "/{id}/mark-printing" })
  .input(z.object({ id: Id }))
  .output(GangSheetDetail)
  .errors({ FORBIDDEN: { status: 403, message: "Company does not print in-house" } }),
markPrinted: proc("production.build")
  .route({ method: "POST", path: "/{id}/mark-printed" })
  .input(z.object({ id: Id }))
  .output(GangSheetDetail),
```
`markPrinting` only succeeds when `company.settings.printsInHouse` is true and the sheet is `ready`; it skips the vendor entirely (no `sent`/`acknowledged`). `markPrinted` moves `printing → printed`; units then flow to the floor exactly as a vendor-printed sheet does — confirm at build time whether the vendor path's existing `printed`-adjacent handling can be reused as-is or needs a small branch for "no vendor on this sheet."

### 4. Bin CRUD + bin/blank labels (T-6-2)
Today's `Bin` (`schemas/production.ts:305`) has no `id`, `name` or archive field — it's occupancy state, not a manageable entity. `bins` (`db/schema/production.ts:195`) does have `id`, so this is a small additive migration (two nullable columns), not a redesign:
```ts
// schemas/production.ts: Bin gains
name: z.string().nullable(),
archivedAt: Timestamp.nullable(),

// contract/production.ts, inside bins router
create: proc("production.build")
  .route({ method: "POST", path: "/" })
  .input(z.object({ code: z.string().min(1).max(40), name: z.string().min(1).max(80).nullable().default(null), locationId: Id.optional() }))
  .output(Bin)
  .errors({ CODE_TAKEN: { status: 409, message: "A bin with this code already exists" } }),
rename: proc("production.build")
  .route({ method: "PATCH", path: "/{id}" })
  .input(z.object({ id: Id, name: z.string().min(1).max(80) }))
  .output(Bin),
archive: proc("production.build")
  .route({ method: "POST", path: "/{id}/archive" })
  .input(z.object({ id: Id }))
  .output(Bin)
  .errors({ BIN_OCCUPIED: { status: 409, message: "Bin holds an order" } }),
/** Replaces the current `list` input: adds includeArchived, and output rows carry name/archivedAt. */
list: proc("production.read", { auth: "floor" })
  .route({ method: "GET", path: "/" })
  .input(z.object({ locationId: Id.optional(), onlyOccupied: z.boolean().default(false), includeArchived: z.boolean().default(false) }))
  .output(z.object({ items: z.array(Bin) })),
labels: proc("production.build")
  .route({ method: "POST", path: "/labels" })
  .input(z.object({ binIds: z.array(Id).min(1).max(200) }))
  .output(z.object({ key: z.string() })),

// contract/inventory.ts, top level under inventory
blankLabels: proc("purchasing.manage")
  .route({ method: "POST", path: "/blanks/labels" })
  .input(z.object({ variantIds: z.array(Id).min(1).max(200) }))
  .output(z.object({ key: z.string() })),
```
Rendering: a new imaging endpoint (e.g. `POST /labels/qr`, alongside the existing `/labels/mock` in `invai-imaging/app/main.py`), taking a list of `{ code, caption, size: "4x6" | "2x1" }` and returning a merged PDF using the existing `qrcode` package (imaging-engineer co-review). Backend calls imaging, `putObject`s the PDF under the tenant's S3 prefix, returns that key.

### 5. `ai.listings.exportCsv` (T-6-4)
```ts
// contract/ai.ts
exportCsv: proc("ai.listings.manage")
  .route({ method: "POST", path: "/listings/export-csv" })
  .input(z.object({ draftIds: z.array(Id).min(1).max(500), channel: z.enum(CHANNELS) }))
  .output(z.object({ key: z.string() }))
  .errors({
    CHANNEL_MISMATCH: { status: 400, message: "A draft's channel does not match the export channel" },
  }),
```
Backend rewrite of `exportCsv()` (`modules/ai/service.ts:650`): signature changes from `(channel, content, sku)` to `(channel, rows: { content: ListingContent; sku: string }[])`, one row per **variant**, not per draft — a draft covering 5 variants expands to 5 rows sharing the draft's copy but each with its own real `catalog.variants.sku` (join via the draft's `designId`/`productId`, the same variants T-6-1 reads as `BlankSummary`). Etsy already has a branch; **Shopify has none today** (falls through to the generic fallback) — add a proper Shopify product-CSV branch (one `Handle` per draft, `Variant SKU`/`Variant Price` per row) before calling AC2 done. This also finishes B-101's line-792 fix, since real SKUs are now a required input, not `DRAFT-${id.slice(0,8)}`.

### 6. `production.reprints.reasonsByWeek` (new — T-6-2's AC2 has no backing endpoint today)
```ts
// contract/production.ts, inside reprints router
reasonsByWeek: proc("production.read")
  .route({ method: "GET", path: "/reprints/reasons-by-week" })
  .input(z.object({ from: Timestamp, to: Timestamp }))
  .output(z.object({
    weeks: z.array(z.object({
      weekStart: DateOnly,
      total: z.number().int().nonnegative(),
      byReason: z.partialRecord(z.enum(REPRINT_REASONS), z.number().int().nonnegative()),
    })),
  })),
```
The existing `reprints.stats` returns one flat total for the whole period; there is no per-week series to chart "count by reason and by week" from.

### 7. `finance.exportCsv` for profit (new — T-6-3's AC3 has no backing endpoint today)
```ts
// contract/finance.ts
exportCsv: proc("finance.read")
  .route({ method: "POST", path: "/profit/export-csv" })
  .input(z.object({
    dimension: ProfitDimension,
    period: Period,
    channel: z.enum(CHANNELS).optional(),
    designId: Id.optional(),
  }))
  .output(z.object({ key: z.string() })),
```
Same filters as `finance.profit`, so the export always matches what's on screen. Drill-down needs no new endpoint — link each row to the orders list, pre-filtered by that row's dimension key and period — but confirm `orders.list`'s filters actually cover a blank/design filter before assuming that at build time; `ProfitSummary` rows are keyed by dimension, not by an `orderIds` array.

## Clarifications from the plan review
- **`printsInHouse` and `SHEET_STATES`/`SHEET_TRANSITIONS` need a grant.** T-6-2's owned paths don't include `invai-contracts` or `modules/tenancy/**`, but exposing the company setting (stub 2) touches `schemas/tenancy.ts`, `contract/tenancy.ts` and `modules/tenancy/service.ts` — all T-6-5's territory this wave. Recommendation: T-6-5 lands the one-field `printsInHouse` addition (it's already touching tenancy for the demo fix) early, or T-6-2 gets an explicit narrow grant to add exactly that field, coordinated so the two cards don't collide on the same lines. Either way, resolve before T-6-2's build starts — it's a blocking dependency, not a nice-to-have.
- **Adding `printing` to `SheetState` needs one more grant.** `invai-web/src/components/badges.tsx`'s `SHEET_TONE: Record<SheetState, Tone>` (outside T-6-2's `routes/_app/production/**`/`features/production/**` glob) will fail `tsc` with a missing-key error the moment the enum grows. Grant T-6-2 that one line, or have it flagged for the tech lead to add.
- **T-6-2 depends on T-6-1's `inventory.blankLabels`.** Bin/blank labels (AC3) call a procedure whose backend lives in `modules/inventory/**`, owned by T-6-1. Both build in parallel per the wave order — treat `inventory.blankLabels` landing as a checkpoint T-6-2 waits on, not an assumption.
- **T-6-1's 15-minute stuck-`submitting` alert (AC3) needs a fake-clock test, not a live wait.** Verify with a backdated `submittedAt`/timestamp fixture, not a real 15-minute sleep in the browser pass.

## Integration gate
- [ ] disk > 5 GB
- [ ] Fresh seed; API, browser and floor E2E pass
- [ ] Builds pass
- [ ] Cleanup
- [ ] Pushed
