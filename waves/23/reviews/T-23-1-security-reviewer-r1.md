# Review: T-23-1 (round 1, security co-review — AC5 files risk flag)
Reviewer: security-reviewer on Sonnet 5
Author: web-engineer on Opus 5.5

## Scope
Co-review of the `files` risk flag only (AC5 buyer-photo upload), plus a check of the other new
file/URL-handling actions (SCAN form PDF download, address check) per the tech lead's brief.

## Verdict: approve

## Evidence I re-ran
- `git -C invai-web show efde2d4` — full diff of
  `src/routes/_app/catalog/personalization.$templateId.tsx`.
- `git -C invai-web diff 54b64d7 353a49d -- vite.config.ts src/lib` — CSP/upload-helper diff.
- `git -C invai-web show 52bd982 -- src/routes/_app/shipping.tsx src/features/orders/order-actions.tsx`
  — SCAN form download and address check.
- Read `invai-web/src/lib/upload.ts`, `src/components/signed-image.tsx`, `src/lib/errors.ts`.
- Read `invai-backend/src/modules/files/service.ts` (`LIMITS`, `presignUpload`, `downloadUrl`,
  `canReadKind`) — confirms server-side type/size enforcement for `kind: "photo"` is unchanged and
  matches the client's accept hint (png/jpeg/webp/heic, 25 MB).
- `grep -n "console\." <touched files>` — no hits.

## Findings: none blocking

## Checklist
- **Existing presigned flow, no new bypass.** `SamplePhotoUpload` calls
  `uploadFile("photo", file)` → `client.files.presignUpload` → PUT → `fileKey`, the same helper
  and the same `files.presignUpload`/`files.downloadUrl` contract procedures every other upload
  screen uses. No new backend route, no new S3 helper. `invai-contracts/src/contract/files.ts` is
  untouched by this card.
- **Server is the authority.** `LIMITS.photo` in `invai-backend/src/modules/files/service.ts`
  (`maxBytes: 25 MB`, `types: /^image\/(png|jpeg|webp|heic)$/`) rejects on `sizeBytes`/
  `contentType` before signing, independent of the client's `accept` attribute, which is only a
  browser hint. The client can't widen this — `presignUpload` throws `FILE_TOO_LARGE`/
  `UNSUPPORTED_TYPE` first.
- **No inline SVG, no `dangerouslySetInnerHTML`.** Grepped the diff and found neither. The preview
  uses a real SVG `<image href={signed.data.url}>` pointing at a signed HTTPS URL from
  `files.downloadUrl`, not markup from the uploaded file. Address-check suggestion text
  (`order-actions.tsx`) renders through plain JSX text nodes (React-escaped), not raw HTML.
- **No object URLs.** The preview uses `useSignedUrl`/`SignedImage` (server-signed URL via React
  Query), not `URL.createObjectURL`, so there is nothing to revoke — this avoids the blob-leak
  class entirely rather than needing cleanup.
- **No PII in logs.** No `console.*` in any touched file. Upload failures go through
  `errorMessage(e)` → `errorInfo()`, which maps errors to a fixed set of translated messages and
  only echoes the backend's `message` field (never the file itself, its key, or buyer data) to a
  toast, not a log sink.
- **CSP unchanged.** `git diff 54b64d7 353a49d -- vite.config.ts` shows only the AC7 `manualChunks`
  bundle-splitting addition; `devCsp`/`prodCsp` and `securityHeaders` are referenced, not edited.
  No widening of `connect-src`/`img-src`.
- **SCAN form PDF download** (`shipping.tsx`): `client.files.downloadUrl({ fileKey, disposition:
  "attachment" })` then `openInNewTab(d.url)` (`window.open(..., "noopener,noreferrer")`) — same
  pattern as existing sheet/label downloads, server-signed URL, no bypass of `isSafeKey`/tenant-
  prefix checks in `downloadUrl` (unchanged backend code).
- **Address check** (`order-actions.tsx`): `AddressSection` is gated by `can("orders.manage")`
  at the top (pre-existing, unchanged) and the "Check address" button by `can("shipping.manage")`.
  The carrier's suggested address (`check.suggestion.*`) renders as plain JSX text/`<address>`
  markup, not HTML injection. `check.detail` (free text from the carrier) is likewise a plain text
  node.

## Optional notes (non-blocking)
- `KIND_PERMISSIONS` in `invai-backend/src/modules/files/service.ts` has no entry for `photo`, so
  `canReadKind` falls through to `true` (any company member with a valid session can read any
  `photo`-kind file in their own company, no extra permission gate). This is pre-existing backend
  behavior, not touched by this card, and is still company-scoped (`owned` prefix check). Not a
  finding against this card; noting only because `photo` files can now include buyer-supplied
  personalization samples — worth a look next time `files/service.ts` is in scope.

## Not re-run
Full `invai-web` typecheck/lint/test/build and the non-files ACs are the primary reviewer's job;
this file covers only the `files` flag and the two other file/URL actions named in the brief.
