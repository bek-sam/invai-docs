# Review of T-9-3 (round 1)

- Reviewer: architect on Sonnet 5
- Author: imaging-engineer on Sonnet
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git diff --stat` for each of the 3 worktrees (imaging@10c1aa2, contracts@2b2f12b, backend@78a0e8f) against the commit before each | Every changed path matches the card's owned/granted files exactly — no drift into `app/compose.py`, `app/vips.py`, other `SheetSpec` fields, or other `main.py` classes that T-9-2/T-9-4 own |
| Read `app/pdf.py` diff, `app/main.py` diff, `src/schemas/vendors.ts` diff, `src/modules/vendors/service.ts` diff in full | Cap replaces the `/UserUnit` branch outright (no dead code left); `PDF_MAX_LENGTH_IN` is a single named constant shared by the imaging-side check and `MAX_PAGE_PT`'s derivation |
| `grep -rn "\.spec\b"` over `invai-backend/src` for every write path to `vendorConnections.spec` | Exactly 2 call sites write it (`inviteVendor` insert, `updateConnection` update); both now call `sheetSpecPdfCapError` before the write. No other writer exists. |
| `uv run ruff check . && uv run pytest -q` at imaging HEAD (`6b9c8f3`, after T-9-2 landed on top) | ruff clean, 51/51 passed — confirms the transient mid-batch stale-test failure at `10c1aa2` alone (see reviewer's file) self-resolved and didn't leak into the batch's end state |
| `tsc --noEmit` at contracts@2b2f12b and backend@78a0e8f | both clean |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Cap (not split) decision applied consistently to contracts + imaging, PDF-only | Yes | Same predicate/message everywhere: `app/pdf.py` (`max(width_in,height_in) > PDF_MAX_LENGTH_IN`), `ComposeRequest._pdf_length_cap` (`pdf_key is not None and length_in > PDF_MAX_LENGTH_IN`), `sheetSpecPdfCapError` (`format === "pdf" && maxLengthIn > PDF_MAX_LENGTH_IN`). PNG is untouched at every layer. |
| 2. Tested split-or-reject at 240in | Yes | Covered by imaging unit tests, the `/compose` 422 test, and 3 backend invite/update tests; new tests fail on base code (verified against `bbb85a3`/`f3b0eea`, see reviewer's file) |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope
- [x] Tests exercise the behavior, none weakened (scan-test-weakening: no hits in any of the 3 repos)
- [x] Tenancy/idempotency/money/en-es — n/a for this card (validation-only change, no new tables or side effects; both spec writes stay inside the existing tenant tx)
- [x] Decisions recorded — cap-not-split rationale is in `wave.md`'s plan review r1 and repeated as a comment at each of the 3 enforcement points

## Architecture-specific review

1. **`sheetSpecPdfCapError()` as a plain function instead of `.refine()`.** The report's stated reason — zod v4 drops `.partial()`/`.pick()`/etc. from an object once it carries a `.refine()`, and `SheetSpec.partial()` is load-bearing for `VendorInviteInput` and the `vendors.update` input outside this card's grant — checks out: I confirmed the same behavior is why T-9-2's `labelGapIn` work also left `SheetSpec` unrefined. Running the check on the *merged* spec (not a partial) is also the only sound option, since a partial update can omit `format` or `maxLengthIn` entirely. This is the right call and correctly narrower than what `wave.md`'s snippet sketched — the snippet was written before that zod constraint was confirmed, and the card record says to "record the decision," which this diff's comments do at all three sites.
2. **Two lines of defense, correctly ordered.** Spec-save (contracts+backend) is the primary gate: a vendor can never persist an over-length PDF spec. `/compose`'s `model_validator` and `app/pdf.py`'s `ImageError` are defensive, in the sequence a request would actually hit them (validate before compositing work starts, then again inside the PDF writer itself). No redundant/contradictory checks.
3. **`NestRequest.max_length_in le=240`.** `/nest` has no `format` field, so it can't distinguish PDF from PNG — the report is upfront about this being a defensive ceiling only. Setting it to PNG's (looser) 240in ceiling rather than PDF's 200in is correct: nesting math is format-agnostic and must not reject a valid PNG-only 240in job; the tighter, format-aware 200in gate lives where format is actually known (`/compose`, spec save). This is consistent with T-9-5's own follow-up plan to add general bounds to `main.py`'s remaining unbounded fields.
4. **Removal, not special-casing, of `/UserUnit`.** Matches the wave-level architectural decision (200in × 72pt = the pre-existing `MAX_PAGE_PT`), so the change shrinks `app/pdf.py` rather than adding a branch. Confirmed no residual `/UserUnit` code path anywhere (grep); the only remaining references are historical/comments plus one unowned stale test that the very next commit removes.

## Optional notes (not blocking)
- Same as reviewer's file: `README.md`'s architecture description of PDF output is stale post-change and the mid-batch shared-working-tree coordination (documented in the report) briefly broke `tests/test_compose.py` at this card's own commit — both worth a follow-up, neither changes the verdict since HEAD is green and the decision/enforcement itself is sound.
