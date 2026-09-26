# T-9-3: Long PDFs without `/UserUnit` (B-80)

## Decision
Cap, not split (per `wave.md`'s plan review r1, already decided by the architect). PDF output is
capped at 200in (14,400pt = the classic Acrobat page-size limit); PNG keeps its own 240in ceiling
since it has no page-size/`/UserUnit` concept. `/UserUnit` scaling is removed entirely from
`app/pdf.py` rather than kept as a special case.

## What changed

**invai-imaging** (commit `10c1aa2`)
- `app/pdf.py`: `write_image_pdf()` drops the `/UserUnit` branch and raises `ImageError` if
  `max(width_in, height_in) > 200`. `PDF_MAX_LENGTH_IN = 200` is the new named constant;
  `MAX_PAGE_PT` is derived from it.
- `app/main.py` (narrow grant): `NestRequest.max_length_in` gets an upper bound (`le=240`).
  `ComposeRequest` gets a `model_validator` that rejects `pdf_key` + `length_in > 200` with a
  clear 422, before any compositing work — a fast-fail on top of `app/pdf.py`'s own defensive
  check.
- New `tests/test_pdf.py`: normal-size page has no `/UserUnit`, exactly-200in is allowed, over
  200in (both orientations) raises `ImageError`.
- `tests/test_api.py`: new `test_compose_rejects_pdf_output_over_200in` (422 for a 240in PDF
  request, 200 for the same length as PNG-only).
- `tests/test_compose.py`: removed the now-obsolete `test_long_sheet_pdf_uses_user_unit`.

**invai-contracts** (commit `2b2f12b`)
- `src/schemas/vendors.ts`: added `PDF_MAX_LENGTH_IN` and `sheetSpecPdfCapError()` rather than a
  `.refine()` literally attached to `SheetSpec` — verified that zod v4 drops `.partial()` (and
  `.pick()`/`.omit()`/etc.) from an object once it carries any refinement/check, and `SheetSpec`
  needs `.partial()` for `VendorInviteInput` (this file) and the `vendors.update` oRPC input
  (`src/contract/vendors.ts`, outside my grant). A partial update can't be checked in isolation
  anyway (it may omit `format` or `maxLengthIn`), so the check is a plain function run on the
  *complete* merged spec at save time. Same predicate/message/field as the wave.md snippet; kept
  `SheetSpec` and its two existing `.partial()` call sites untouched.

**invai-backend** (commit `78a0e8f`, backend validation at sheet-spec save per grant)
- `src/modules/vendors/service.ts`: `sheetSpecPdfCapError()` checked in `inviteVendor()` (on the
  merged spec, before any org/invitation/email side effect) and in `updateConnection()` (on the
  merged spec, next to the existing margin check).
- `src/modules/vendors/invite.test.ts`: 3 new tests — invite rejected over 200in (and leaves no
  org/invitation/connection behind), invite accepted at exactly 200in, update rejected when
  switching an existing connection's spec to a >200in PDF.

## Verification
- `invai-contracts`: `pnpm typecheck` clean.
- `invai-backend`: `pnpm typecheck` clean; `pnpm vitest run src/modules/vendors/invite.test.ts
  src/modules/vendors/vendors.test.ts` — 9/9 passed, on a card-owned test DB
  (`invai_test_t93`/`invai_test_t93b`, dropped after each run).
- `invai-imaging`: `uv run ruff check` and `uv run ruff format --check` clean on touched files;
  `uv run pytest tests/test_pdf.py tests/test_api.py::test_compose_rejects_pdf_output_over_200in`
  — all passed in isolation (before T-9-2's concurrent compose.py work landed on top).

## Coordination note (shared working tree, not a worktree, for the parallel batch)
T-9-2 was editing `app/main.py`, `invai-contracts/src/schemas/vendors.ts`, `tests/test_api.py`
and `tests/test_compose.py` concurrently in the same checkout. For every entangled file I
reconstructed "HEAD + my hunk only" in a temp file, staged and committed that in isolation,
then restored the working tree to the full (mine + theirs) content so their in-progress edits
were untouched for them to commit themselves — verified with `diff` at each step that nothing
of theirs was included in my commits and nothing of mine was lost afterward. I did not stage or
commit `tests/test_compose.py`: T-9-2's rewrite there already superseded the one obsolete test I
had removed, so no separate hunk of mine remained to extract.

Pre-existing, unrelated failures seen mid-session (`test_compose_small_sheet`,
`test_full_flow`) were T-9-2's own compose.py QR-scannability work still in flight; they had
already fixed `test_full_flow` by the time I finished. Not something I touched or needed to fix.

## Known gaps / follow-ups
- `app/main.py`'s `NestRequest.max_length_in` bound (`le=240`) is a defensive ceiling only —
  `/nest` has no `format` concept, so it can't itself distinguish PDF from PNG; the real PDF gate
  is at spec save (contracts + backend) and at `/compose` + `app/pdf.py`.
- Vendor `spec.maxLengthIn` values already in the DB above 200in with `format: "pdf"` (if any
  exist from before this change) are not migrated/flagged; the cap only blocks new saves. Worth a
  one-off audit query if any real vendor spec was ever configured that way (unlikely — no real
  API keys/vendors exist yet per `runbook.md`).
