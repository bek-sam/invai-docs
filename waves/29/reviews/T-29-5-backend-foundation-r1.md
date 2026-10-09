# T-29-5 backend-foundation consumer co-review, round 1
Reviewer: backend-foundation (Opus 5.5). Author: architect. Contract 0.13.0 -> 0.14.0. Read-only; no backend typecheck run (T-29-1 tree in progress).

## Verdict: approve

## Findings (backend side)
- DB: `order_items.artwork_status` is `text DEFAULT 'none' NOT NULL` (drizzle/0000_init.sql:534). No CHECK or pg enum on it anywhere; `enumText()` is type-only. 'purged' is accepted by the DB; no migration needed.
- Type mirrors: `ITEM_ARTWORK_STATUSES` (src/db/schema/orders.ts:163) and `ARTWORK_STATUSES` (personalization.ts:68, the separate item_artwork table status, not touched by the contract diff) are local const arrays. The orders mirror lacks "purged" until T-29-1/B-side adds it; it only narrows the column type, so no runtime break. Suggest T-29-1 append "purged" there (type-only).
- Readers: no exhaustive switch or Record keyed by artwork status in src (grep). production/sheets.ts:169 allows only rendered/approved, so a purged personalized item falls to `needs_artwork` (correct, matches "re-enter to print again"). views.ts:252 and orders/service.ts:278 pass status through to ItemArtworkSummary, which now accepts purged. preview-backfill.ts:31 filters on "none" only.
- Writers: only set none/pending/approved/outcome.status; nothing writes purged yet (T-29-1 will).
- Enum append is last, old values order-preserved (test asserts it); additive, so old clients are unaffected apart from the documented `counts` literal note.

## Commands run
- git -C invai-contracts diff dc62328..0f666f1 --stat and -- src (6 files, +45/-3)
- grep -rnE "ITEM_ARTWORK_STATUSES|artworkStatus|ItemArtworkSummary|artwork_status" invai-backend/src; grep artwork_status drizzle/*.sql (1 hit, the column def)
- grep for Record<...artwork>, CHECK constraints on artwork: none

## Optional notes
- The router.ts:30 errors are T-29-1's to fix; not evaluated here.
