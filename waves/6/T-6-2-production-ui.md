# T-6-2: Production UI: in-house printing, reprints, bins and labels
Scope: items 4 and 5. Backlog: B-87.

## Owned paths
- web: the production routes and features, own i18n keys
- **grant needed:** `invai-web/src/components/badges.tsx`'s `SHEET_TONE` map (one new `"printing"` key — adding it to `SheetState` breaks `tsc` there otherwise), and a narrow, coordinated grant into `invai-contracts` (`schemas/tenancy.ts`, `contract/tenancy.ts`) plus `invai-backend/src/modules/tenancy/service.ts` for the one-field `printsInHouse` addition — or T-6-5 lands that field itself since it's already touching tenancy this wave. Resolve before build starts; see `wave.md`'s "Clarifications from the plan review."
- backend: `modules/production/**` (the in-house transitions, the bin and blank label procedures, plus a small additive migration on `bins` for `name`/`archivedAt`)
- imaging: a new label render endpoint (imaging has `qrcode`; backend Node does not — labels render in imaging, not as a backend PDF) (imaging-engineer co-review)
- depends on: T-6-1's `inventory.blankLabels` (owned by `modules/inventory/**`) landing before/alongside this card's blank-label work
- tests

## Acceptance criteria
1. **In-house printing:** with the company setting `printsInHouse` (see `wave.md` stub — needs a grant), a ready sheet can be marked "printing" via `production.sheets.markPrinting`, then "printed" via `markPrinted`, with no vendor step. After that the units move to the floor as usual. The vendor path is unchanged. `SHEET_STATES`/`SHEET_TRANSITIONS` gain `printing` between `ready` and `printed` (exact shape in `wave.md`).
2. **Reprint queue:** a list with filters, cancel, and a reasons report showing count by reason and by week, via the new `production.reprints.reasonsByWeek` (exact stub in `wave.md` — today's `reprints.stats` only returns one flat total for the period, with no per-week series).
3. **Bins:** list, create, rename and archive bins. Today's `Bin` schema has no `id`/`name`/archive field (it's occupancy state, not a manageable entity); add `create`/`rename`/`archive` procedures and `name`/`archivedAt` columns (small additive migration — exact shapes in `wave.md`). Print `BIN:` QR labels (a 4x6 or 2x1 PDF, via `production.bins.labels`) and `B:<variantId>` blank labels for chosen variants (via T-6-1's `inventory.blankLabels`). Both return an S3 key (`files.downloadUrl`), not a new "file id" concept. The labels must scan on the floor, which already reads `B:` and `BIN:`.
4. **Quality:** en and es, 390 px, keyboard accessible.

## Verify
Run tsc, lint, test and build (plus imaging ruff and pytest if touched). Browser pass on a DB copy: the in-house path on one sheet, a reprint cancel, the reasons chart, and a bin label PDF that decodes to the right QR (check with a script). At most 6 screenshots.
