# Security co-review: T-P5-2 (round 1, files flag)

- Reviewer: security-reviewer on Opus 5.5
- Author: backend-engineer on Opus 5.5
- Verdict: **approve**

## Threat model
Entry point: `catalog.updateDesign` (`catalog.manage`, session auth) and the internal
`renderDesignPreviews` call. Worst case if wrong: cross-tenant object deletion (shop A's replace
deletes shop B's file) or deletion of a non-preview object (original art, a sheet, a label) — both
High. Checked both paths end to end against `git -C invai-backend show 0aa67d8`.

## Deletion can't cross tenants or hit a non-preview object
- Candidate keys come from `tx.select(designFiles.previewKey).where(eq(designId, input.id))`
  inside the request's own `withTenant(ctx.companyId)` transaction (RLS-scoped already), then
  filtered again by `isCompanyKey(ctx.companyId, k) && k.startsWith(\`${cid}/preview/design/\`)`
  (`service.ts:247-254`). Two independent barriers to a cross-tenant key.
- `designFiles.previewKey` is written in exactly two places in the whole backend:
  `catalog/service.ts:477` (via `designPreviewKey(companyId, fileId)`) and
  `db/seed/builder.ts:546` (same helper). No user input ever reaches this column — confirmed by
  grepping every `update(designFiles)` call site (the other one, `service.ts:376`, sets `fileKey`/
  QA fields only, never `previewKey`). So the prefix/isCompanyKey filter can never today diverge
  from "always true" — it is real defense-in-depth against a future bug, not a currently-live
  control, which matches the primary reviewer's "code-read only, no test" note (optional note 2).
- `cleanupOldPreviewKeys`'s reference re-check (`service.ts:280-305`) runs in a fresh
  `withTenant(companyId)`, so it is RLS-scoped to the same company as the candidate keys; there is
  no column anywhere that could make another company's row match (keys are company-prefixed
  strings, and the read is tenant-scoped besides). `deleteObject` is only ever called on keys from
  this candidate set.

## Reference check reads under the right tenant
Confirmed `cleanupOldPreviewKeys` opens its own `withTenant(companyId, …)` (not `withSystem`), and
checks all four R2 columns (`design_files`, `order_items.artwork_preview_key`,
`item_artwork.preview_key`, `gang_sheets.preview_key`) before deleting. RLS makes it impossible for
another company's reference row to suppress or force a delete here.

## Backfill UPDATE is company-scoped
`backfillItemPreviews` (`orders/preview-backfill.ts`) runs inside the caller's `withTenant(companyId)`
tx *and* adds an explicit `eq(orderItems.companyId, companyId)` — belt-and-suspenders, matches the
existing pattern elsewhere. The `previewKey` it writes is always `out.out_key` from the same
company's `designPreviewKey(companyId, file.id)` call in the same transaction — no path for it to
carry another company's key. The cross-tenant test (same `designId` value in two companies) passed
and is a real check, not vacuous: it exercises the `company_id` filter against a same-id collision.

## No PII
No buyer data is read or touched by this change; log line is `{ companyId, error }` only.

## On the primary reviewer's note (no test for the prefix check)
Not blocking. As shown above, there is no live code path today that makes the filter's absence
observable — a mutation test removing it would currently pass against head and base identically
on the given test set, because every `previewKey` in the DB already satisfies it. I'd still ask for
one regression test (a row with a non-preview-shaped key in `design_files.preview_key`, e.g. via a
direct `tx.update`, to prove the filter itself fires) as a low-priority follow-up — not a gate for
this card.

## Checks re-run
Read-only; no new worktree needed — verified by code inspection plus the primary reviewer's
mutation-tested run (`vitest run src/modules/catalog src/modules/orders/preview-backfill.test.ts`,
25/25 passed) and the author's live curl exercise (prefix count 41→40 on delete, `exists:true` kept
when referenced, presser `403 FORBIDDEN`). No reason to doubt that evidence; no process started.

## Findings
None blocking. One optional hardening suggestion (prefix-filter regression test) — not a security
finding, no `v1-review.md` entry warranted (no exploitable gap exists in the current code).

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
