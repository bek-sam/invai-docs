# T-7-1: Tracking export files for CSV channels (B-68)
## Owned paths
- backend: new `integrations/channels/exports/**`, `modules/shipping/**` (export procedure only)
- backend: `db/schema/shipping.ts` (new `shipments.exportedAt` column only — grant, see `wave.md` clarifications) and `invai-contracts` (the matching `exportTracking` procedure, and `NormalizedOrder.sourceUpdatedAt` on T-7-4's behalf — see below)
- web: `routes/_app/shipping.tsx` (export button only), own i18n keys
- tests

## Clarifications from the plan review
- Exact shapes for `exportTracking` and `shipments.exportedAt` are in `wave.md` under "Contract stubs (exact)" §1. Don't reuse `trackingPushStatus`/`trackingPushedAt` for the export marker — B-67 already shows `manual` conflated with "pushed" in void logic; `exportedAt` is its own re-settable timestamp.
- `integrations/channels/pending.ts` (the manual-upload message, B-68's cited file) isn't in this card's owned paths but its copy should point at the new export button once it exists — small addition here, not a separate grant.
- **Cross-card ask:** while you're already touching each CSV/Shopify adapter's `normalize()` for this card, also set `sourceUpdatedAt` (new field, stub §3 in `wave.md`) per adapter — T-7-4 owns the contract field and the orders-side staleness check, but populating it per-channel lives in your `integrations/channels/**` territory. Coordinate with T-7-4 so you don't collide on the same adapter files.

## Acceptance criteria
1. **Export files:** for each CSV-only channel, generate the upload file in the marketplace's own format:
   - Etsy: orders and tracking bulk upload;
   - Amazon: shipping confirmation flat file;
   - TikTok Shop: bulk shipping;
   - Walmart: shipment update.
   Each file covers shipments labeled since the last export, or a chosen date range, with carrier code mapping per marketplace. Verify every format against the marketplace's current docs (cite the source and date in the report).
2. **Status:** the export marks those shipments `exported_at`, and re-export is possible. Once exported, shipments show as "tracking uploaded (manual)".
3. **Web:** an "Export tracking for <channel>" button on the Shipping page, with a count, and the file downloads. Short instructions (en/es) explain where to upload it.
4. **Tests:** fixtures for each format.

## Verify
Run tsc, lint, test and build. On a DB copy: label 3 Etsy orders, export, and check the CSV columns against the doc.
