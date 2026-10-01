# T-P1-2 security-reviewer review (round 1)

Reviewer: security-reviewer on Claude Sonnet 5. Author: imaging-engineer on Claude Opus 5.5.
Primary reviewer (`reviewer`) approved in r2. This co-review covers the `files` flag only: the
new `POST /preview`.

**Verdict: approve**

## Scope
Diffs `2fc3806` (AC0, `/preview` alone), `f77e6e8` (rest of card), `26699d8` (round-2 fix to the
photo-flag codes — not a `files`-flag concern, not re-audited here). Card:
`invai-docs/waves/P1/T-P1-2-imaging-polish.md`. Report:
`invai-docs/waves/P1/reports/T-P1-2.md`.

## Checks re-run
- `cd invai-imaging && uv run pytest -q` → `119 passed` (matches the report).
- Live on `:8053` (`STORAGE=local`), scratch dir `/tmp/invai-imaging-secrev-local`, PIDs 78092/78094, both killed, scratch dir removed, port confirmed free after.

## Findings

**1. Shared-secret auth — same as `/compose`. Pass.**
`GuardMiddleware` (`app/guard.py`) is deny-by-default: every path except the `/health` allowlist
entry requires `X-Imaging-Secret`. `/preview` was not added to `OPEN_PATHS`, so it inherits the
check automatically; no route-specific wiring was needed or added. Verified live:
`POST /preview` with no header → 401; wrong secret → 401; correct secret → 200. Matches the
existing test pattern (`tests/test_limits.py` exercises the mechanism via `/nest`/`/compose`,
which is sufficient since the middleware is path-agnostic by construction).

**2. Key validation / storage helper — same as every other route. Pass.**
`file_key`/`out_key` use the same `Key = Field(min_length=1, max_length=512)` as every existing
endpoint, and the handler calls `_download()`/`get_storage()` unchanged — no new key shape, no
bypass of `_CheckedStorage`'s magic-byte check.

**3. `out_key` can write into another company's prefix — true, and not new.**
Live test: `file_key=companyA/design.png`, `out_key=companyB/stolen-preview.png` →
`200 {"out_key": "companyB/stolen-preview.png", ...}`, file written under `companyB/`. Imaging
has **no** company-prefix check anywhere (`Key` is pure length validation) — this is the
existing, accepted model for every endpoint (`/compose`, `/qa/clean-alpha`, `/nest`, ...), not a
regression introduced here. `security/v1-review.md` S-11/S-12 already document that the
`isCompanyKey()` enforcement point is the **backend**, before it calls imaging, not imaging
itself. The card correctly scopes backend wiring to T-P1-4 and out of scope here.
**Action for T-P1-4 (not blocking this card):** the backend's `/preview` client must call
`isCompanyKey()` on **both** `file_key` and `out_key` against the caller's own company before
invoking imaging, the same way `designs.create/update` do post-S-11. Flagging to the tech
lead/architect so T-P1-4's card carries this as an explicit acceptance criterion.

**4. Decompression bomb / pixel limits. Pass, inherited unchanged.**
`/preview` calls the existing `load()` (header-only parse, pixel budget checked before any pixel
is decoded) and, for PDF, the existing `pdf_page_budget_error()` (checked from page size x DPI
before pdfium renders). No new bomb surface: `/preview` adds no decode path of its own. Live
check: a PNG header declaring 60000x60000px (3.6B px) with near-empty IDAT → 422 "over the 570M
pixel limit" in 12ms (no decode attempted). PDF-page-over-budget is already covered by
`tests/test_limits.py::test_pdf_page_over_budget_is_refused_before_render` (119/119 green,
re-ran).

**5. ICC handling — untrusted embedded profile. Pass, with one Low note.**
`to_srgba()` only calls `icc_transform` when `icc-profile-data` is present, and wraps the call in
`try/except pyvips.Error`, falling back to the pre-existing naive `colourspace()` conversion on a
profile vips can't parse (`tests/test_vips.py::test_unparseable_embedded_profile_does_not_fail_the_conversion`,
re-ran green) — so a malformed/garbage profile is never fatal and is never silently applied
incorrectly. **Low, non-blocking:** there is no explicit size cap on the embedded ICC profile
bytes before calling `icc_transform`, and no per-call timeout, so a very large but
well-formed profile (oversized LUT tables) could add outsized latency; `/preview` is also not in
`HEAVY_PATHS`, so it isn't covered by the per-process heavy-job concurrency limiter the way
`/compose`/`/render/personalization` are, meaning many parallel `/preview` calls each paying an
ICC transform aren't throttled. Mitigated in practice because the backend's presigned PUT already
binds the exact object size at upload (per the security brief), bounding how large any embedded
profile reaching imaging can be — and this is consistent with the same trust-the-decoder model
every other raster/PDF/SVG path already relies on (libvips/pdfium), not a new exposure. No crash
or hang reproduced in this review's time budget. **Recommendation (track, don't block):**
imaging-engineer/platform-sre consider adding `/preview` to `HEAVY_PATHS` (or a lighter sibling
limit) and a byte-size cap on `icc-profile-data` before transforming it.

**6. Round-1 blocking finding (photo-flag codes breaking the backend's closed enum) — not a
`files`-flag item, but confirmed fixed and tested** (`26699d8`, `photo_flags` opt-in, default
response byte-for-byte unchanged).

## Blocking findings
None.

## Non-blocking (owner to track)
- T-P1-4 must add `isCompanyKey()` checks on both `file_key` and `out_key` before calling
  `/preview` — give it an explicit acceptance criterion on that card.
- Low: no ICC-profile size cap / timeout and `/preview` outside `HEAVY_PATHS`; propose to
  imaging-engineer as a follow-up, not a fix clock item (no reproduced hang, mitigated by
  upstream exact-size binding on upload).
