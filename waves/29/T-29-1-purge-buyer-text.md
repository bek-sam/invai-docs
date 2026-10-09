# T-29-1: Purge personalization text, rendered art and free-text notes on the PII clocks

| Field | Value |
|---|---|
| Wave | 29 |
| Scope ref | `always-in-scope: security / compliance` (S-56 Medium, due 2026-11-08; Amazon DPP 30-day PII and 18-month rules) |
| Spec | none; source: `security/v1-review.md` S-56, `waves/28/reviews/T-28-3-compliance-officer-r1.md` (answer + finding 1), decisions 0026, 0029; backlog B-293, B-296; plan reviews `reviews/plan-pm.md`, `reviews/plan-architect.md` items 1–6 |
| Owner | backend-engineer (area: privacy, plus the buyer PII purge in orders and the artwork rules in personalization) |
| Reviewer | reviewer (fable) |
| Co-reviewers | security-reviewer (opus), compliance-officer (sonnet), architect (sonnet, consumer of T-29-5's `purged` status) |
| Risk flags | pii, tenancy, files, data deletion, floor-correctness |
| Model | opus |

## Owned paths (edit)
- `invai-backend/src/modules/privacy/**` (in `security.test.ts` only flip the S-56 `it.fails` to `it`)
- `invai-backend/src/modules/orders/jobs.ts` and its test (`purgeBuyerPii` and its selection)
- `invai-backend/src/modules/personalization/**` (the `counts` literal ~service.ts:790, `approve` on a purged row, deleting the previous render key on re-render)
- `invai-backend/src/db/schema/personalization.ts` and `src/db/schema/orders.ts`: the `ITEM_ARTWORK_STATUSES` type-only mirrors (~:68, ~:163) only. The column is text, so no migration
- `invai-backend/src/modules/production/**`: tests only (the existing check at `production/sheets.ts:169` is the guard)
- `invai-docs/decisions/0027-buyer-text-retention.md` (new, type security, status proposed; security and compliance accept) and its index row in `invai-docs/decisions/README.md`. Decision 0026 stays unchanged

## Read-only paths
- everything else in `invai-backend` (`src/db/client.ts`, `src/lib/**`, `src/auth.ts`: T-29-2 works there; `modules/channels/**`: T-29-4), `invai-contracts/**`, `invai-web/**`, `invai-floor/**`

## Depends on
- T-29-5 (architect): the additive contract commit with `purged` in `ITEM_ARTWORK_STATUSES` and `ItemArtworkSummary.status`. Contracts are linked (`link:../invai-contracts`), so no pin: start by reading and planning, change types once T-29-5 is committed.

## Interfaces promised
- `redactBuyerText(tx, orderIds, { scope: "shipped-items" | "all" }) -> { personalizedItems, artwork, notes, files: string[] }` in `modules/privacy/service.ts`, used by `redactOrders` (18-month sweep, Shopify redact, Amazon path; scope `all`) and by the 30-day `purgeBuyerPii` (scope `shipped-items`).
- **Storage first.** Objects are deleted before the DB redaction. An item whose object delete failed is left out of this run's DB redaction (it keeps its keys and status), so the next night finds it again. No new table.

## Acceptance criteria
1. **30-day clock, per item.** Orders are selected from the order clocks (`delivered_at`, `shipped_at`, `cancelled_at`, or `buyer_pii.purge_after` when the row exists, as today's rules), where something is still unredacted; orders whose `buyer_pii` is already gone are covered on the first run (proven by a test). For each such order, only items in `shipped`, `delivered` or `cancelled` are cleared; other items keep their text and art until a later night. For a cleared item:
   - `order_items.personalization` answers and file URLs are null;
   - `item_artwork.values` is `{}`, `flags` is `[]`, `error` is null, status `purged`; `file_key` and `preview_key` objects and any photo-slot value objects (buyer photos stored as keys, ~personalization/service.ts:272) are deleted from storage and the columns are null;
   - on the item, `order_items.artwork_key` and `artwork_preview_key` are null, `artwork_status` is `purged`, and its artwork flags are dropped. The existing check at `production/sheets.ts:169` is then the one "never on a sheet" guard (no new guard).
   - Order facts (ids, SKUs, amounts, dates, states, template id) stay. For cancelled orders the clock starts at `cancelled_at` (state it in decision 0027).
2. **Notes (B-296).** On the same 30-day order clock and in `redactOrders`, free text a person typed that may name the buyer is set to null: `orders.buyer_note`, `orders.hold_note`, `orders.cancel_note`, `refund_events.note`, `reprints.note`. Enum reasons and money stay. Station maintenance notes and `gang_sheets.vendor_notes` are about machines and sheets: leave them and say so in decision 0027.
3. **18-month sweep, Shopify redact, Amazon path.** `redactOrders` calls the helper with scope `all`, so every item is cleared. The S-56 proof in `privacy/security.test.ts` passes as `it`.
4. **Re-entry.** `personalization.artwork.approve` on a purged row answers `CONFLICT`; `update` (new values, re-render) is the re-entry path. A purged item that is reprinted or still in production shows `needs_artwork` in the batch preview. No new error code or copy.
5. **Superseded renders.** From now on a re-render deletes the previous `file_key`/`preview_key` object after the new one is stored. Legacy orphaned renders: add a backlog line in the report, don't build a sweep.
6. **Idempotent and isolated.** Running either purge twice gives one effect and no errors; a second company's orders are untouched (tenant test); a storage delete failure leaves that item for the next night (test).
7. **Not due yet.** An item inside its clock keeps its text, art and notes.
8. **Decision 0027** (security, proposed) lists each field, its clock (30 days, 18 months, redact request) and the keep list with reasons; it says it narrows decision 0026's keep item for refund notes; it records as known gaps with owners: `audit_log` `artwork.rendered` `data.flags` quotes values (append-only), gang sheet print files hold rendered text (`PII_OBJECT_KINDS` is `raw,csv,label`), legacy orphaned renders. Links S-56, B-293, B-296 and the compliance answer.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test` in `invai-backend` (full suite once, at the end, log to a file, `set -o pipefail`).
- Exercise for real with a `tsx` script against `invai_test` or a scratch DB (never the shared `invai` dev DB; pin `REDIS_URL=redis://localhost:6379/12` and `SEED_OUTPUT_FILE=/tmp/...`): a two-item personalized order with rendered art in MinIO, one item delivered and one in production, aged past the clock; run `purgeBuyerPii` twice; show the DB columns, that the shipped item's MinIO objects return 404 and the other item's still exist; show the purged item is not eligible for a sheet.
- Prove each new test red on `origin/main` (the reviewer re-runs that in a worktree).

## Out of scope
- Gang sheet print files, legacy orphan renders, the audit-log copy (backlog lines and decision 0027 gaps only).
- Item titles and the 0026 keep list (OI-19, counsel).
- B-295 notes. Any web or floor change (web keys are in T-29-3).

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
