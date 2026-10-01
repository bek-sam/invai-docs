# Plan review: wave P5 (architect, design)
Reviewer: architect (opus). Verdict: **approve-with-changes** (the changes are the rulings below; cards stand as written).

## R1 (T-P5-3/4/5) Contract shape, contract 0.11.0, purely additive
**Alert** gets two optional fields (both or neither): `messageCode: AlertMessageCode` and `params: AlertParams`. `kind` alone can't pick a line: `tracking_push_failed` carries 5 different texts (3 shipping stuck intents, 2 vendor email outcomes) and `sync_broken` 3, and `plan_limit_reached` has a "near" and a "reached" title. So the line comes from a new enum `ALERT_MESSAGE_CODES`; `ALERT_KINDS` doesn't change. `AlertParams` is one object where every key is optional (the `DigestActionParams` precedent). `ALERT_MESSAGE_PARAM_KEYS` (code → keys) is exported so backend tests and the web read one list. Dates are ISO; the web formats them with `Intl` in `timeZone`.
| messageCode | raised in | params keys |
|---|---|---|
| order_at_risk | today `generateAlerts` | orderNo, shipBy, timeZone, hours |
| order_overdue | today | orderNo, shipBy, timeZone |
| sync_broken | today | connectionName (`last_error` stays in `message` only: provider text, not translatable) |
| sheet_stuck | today | sheetName, hours, sheetStatus (`sent`/`acknowledged`) |
| stock_low | today | blankName, available, reorderPoint, incoming (0 when none) |
| plan_limit_near / plan_limit_reached | today (ratio ≥ 0.9 / limitReached) | usedPct (near only), used, limit, planName |
| label_buy_stuck / label_void_stuck / tracking_push_stuck | shipping/jobs.ts `alertStuck` (buy/void/push) | none (`{}`) |
| vendor_email_unconfirmed / vendor_email_failed | vendors/delivery.ts (outcome unknown/failed) | sheetName, vendorName |
| po_stuck_submitting | inventory/jobs.ts | poNo, supplierName |
| webhook_stuck | channels/jobs.ts | channel |
Backend storage (T-P5-4, no migration): `AlertInput` gets optional `messageCode` + `params`. `raiseAlert` writes them to `alerts.data.messageCode` / `alerts.data.params`, nested so the keys can't collide with the existing `data` keys (`available`, `intent`, `deliveryId`…), and the upsert keeps them up to date on re-raise. `toAlert` returns both only when the code is known and `AlertParams.safeParse(params)` succeeds; otherwise it leaves both out, so old rows still show title/message. Worker/AI alerts stay title-only.

**TimelineEntry** gets optional `reasonCode: TimelineReasonCode` and `reasonParams: TimelineReasonParams` (typed object, every key optional: `sheetName`, `reprintReason` ∈ REPRINT_REASONS, `holdReason` ∈ HOLD_REASONS, `cancelReason` ∈ CANCEL_REASONS). Only `state_changed` entries carry a reason (item_transitions.reason). T-P5-4 maps the stored reason to a code at read time in `orders/service.ts`. Rules, in order:
1. reason null/empty → no code.
2. `to = on_hold` and reason ∈ HOLD_REASONS → `held` {holdReason}; `to = cancelled` and reason ∈ CANCEL_REASONS → `cancelled` {cancelReason}. The state decides first because `buyer_request`/`out_of_stock`/`other` are in both lists.
3. Exact strings: `unknown_sku`, `mapped`, `not_personalized`, `artwork_uploaded`, `artwork_approved`, `artwork_edited`, `artwork_rerendered`, `artwork_rendered`, `artwork_failed`, `artwork_flagged`, `released`, `qc_fail` (seed) → the code of the same name. `scan match` → `scan_match`, `QC pass` → `qc_pass`, `tracking pushed` → `tracking_pushed`, `carrier accepted the package` → `carrier_accepted`, `carrier delivered` → `carrier_delivered`.
4. Patterns: `^on sheet (.+)$` → `on_sheet` {sheetName}; `^sheet (.+) received$` → `sheet_received` {sheetName}; `^reprint: (.+)$` → `reprint` {reprintReason only if it is in REPRINT_REASONS, otherwise the code goes out without the param}.
5. Anything else → no code (`message` unchanged, web falls back to `extractTimelineReason`).
Producers: orders/import.ts:357,714, mapping.ts:136,144, service.ts:756,787,975,1148, personalization/service.ts:673-886, production/floor.ts:505,633,710, sheets.ts:640,1072, shipping/service.ts:1658,1799,1829,1838, db/seed/builder.ts:1052,1078. Anyone who adds a reason later adds its code at the end. Consumers must treat an unknown code like "no code" (look it up in a Record with a fallback, never an exhaustive switch). This keeps lesson A2 from biting later.

## R2 (T-P5-2) Preview cleanup and late backfill
- A design preview key is `${cid}/preview/design/${designFileId}.png` (`designPreviewKey`). It can be referenced only by `design_files.preview_key` and `order_items.artwork_preview_key` (mapping.ts:114 copies it). Also check `item_artworks.preview_key` and `gang_sheets.preview_key` (cheap; their keys use other prefixes today). Any item state counts, shipped included: history thumbnails.
- The rule: `updateDesign` collects the old rows' `preview_key`s inside its transaction, before the `delete(designFiles)`. A key is a candidate only if `isCompanyKey(cid, key)` holds **and** it starts with `${cid}/preview/design/`, so an original, a sheet or a label can never be deleted. `afterCommit(tx, …)` then opens a fresh short `withTenant` read that drops every key still referenced in the four columns, and calls `deleteObject` for the rest outside any transaction. A storage error is a warn log, never a failed update.
- Use afterCommit, not the event payload. The relay collapses two `design.updated` events into one pending `design-preview-${designId}` job (`outbox-relay.ts:33`), so keys carried in the payload would be lost. afterCommit also needs no contract change. Known gaps (report, don't fix): a crash between commit and hook leaves an orphan (that is the out-of-scope sweep); a mapping transaction that read the old file row and commits after the check keeps a dead key (small window).
- Late preview: `renderDesignPreviews` makes a direct call, in the same short `withTenant` transaction that writes `design_files.preview_key`, to a new `orders/preview-backfill.ts` export `backfillItemPreviews(tx, companyId, { designId, placement, previewKey })`. It runs `UPDATE order_items SET artwork_preview_key = $key WHERE company_id = $cid AND design_id = $designId AND placement = $placement AND artwork_preview_key IS NULL AND artwork_key IS NULL AND artwork_status = 'none'`. The `IS NULL` guard makes it idempotent. No outbox event and no subscriber: a new event would be a contract change and a second job for a single-row write.

## R3 (T-P5-1) Seed previews: keep the direct call
`renderDesignPreviews` can't be called from the seed as it is. It opens its own `withTenant` transactions, so it can't see the design rows the seed writes inside `opts.run` before commit. It forces `allowPlaceholder: false`, so with imaging down it throws, and the offline seed would lose its gray thumbnails. That breaks AC5 ("keep today's behavior"). Adding a placeholder option would be a catalog change, which is T-P5-2's path. **T-P5-1 keeps `imaging.preview` with `designPreviewKey`** (already the catalog's key helper) and writes this reason in its report.

## Ownership and missing paths
- T-P5-3 has to bump `invai-contracts/package.json` (0.10.0 → 0.11.0; `compat.test.ts` pins pkg = CONTRACT_VERSION), which sits outside `src/**`. It's the architect's path; I take it.
- T-P5-4: the `messageCode`/`params` plumbing lives in `today/service.ts` (owned). `shipping/jobs.ts` `STUCK_ALERTS` is the alert input. Both fine.
- No clashes: T-P5-2 = catalog/** + mapping.ts + preview-backfill.ts; T-P5-4 = orders/service.ts + today/**; T-P5-1 = seed/**. T-P5-5: the bell (`app-frame.tsx`) only shows a count, so nothing outside its paths.
- Floor reads neither Alert nor TimelineEntry (grep), so the floor stays unchanged.
