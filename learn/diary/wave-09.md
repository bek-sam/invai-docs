# Wave 9 — imaging for real print shops

**Dates:** 2026-09-26 to 27. **Gated:** the combined "wave 6–9" gate — the first time all
three golden-path suites (API, browser, floor) were fully green together.

## What was built
- **T-9-1** PDF and SVG input at target DPI (imaging-engineer): shops can upload designs
  as PDF or SVG, not just raster images, rendered at the real print DPI.
- **T-9-2** Sheet barcode, scannable QRs, label gap (imaging-engineer): gang sheets print
  with a scannable order QR and the physical gap a label needs to not get cut off.
- **T-9-3** Long PDFs without `/UserUnit` (imaging-engineer): very long print files no
  longer break on PDFs that skip the `/UserUnit` field most tools assume is there.
- **T-9-4** Personalization upgrades (imaging-engineer + web-engineer): a template editor
  for per-order text/image personalization (names on a gang sheet, etc.).
- **T-9-5** Imaging limits and service auth (imaging-engineer + platform-sre): the imaging
  service gets real request limits, concurrency bounds and its own auth, so it can't be
  hammered or called by anything outside the backend.

## Why
Imaging is where a digital order becomes a physical, printable file. Everything before
this wave assumed clean raster uploads at the right DPI; real shops hand InvAI PDFs, SVGs,
oddly-encoded long sheets, and expect the gang sheet's QR codes to actually scan on a
real printer and a real phone — not just exist in the file.

## What went wrong
- The combined gate (`waves/9/gate.md`) was the first wave to get **all three golden-path
  suites fully green at once** (API 13/13, browser 15/15, floor 3/3), and confirmed both
  of wave 7's gate-blocking bugs (vendor portal inbox, Etsy AI draft validation) were
  fixed. It also confirmed T-13-5's seed-speed fix landed early (~25s vs. wave 7's
  15–20 minutes) and that `/livez`/`/readyz` and the NUL-byte input boundary worked.
- But it still found two new, wave-9-specific bugs and recommended **not pushing yet**:
  - **Finding B** (hard, 100% reproducible): PDF design uploads always failed QA, because
    `qa.check()` never computed or passed `target_dpi` at all.
  - **Finding A** (subtler): the header QR on a gang sheet silently drops on any realistic
    multi-order sheet. No automated suite caught it, because the suites only exercise
    deep-linked/API paths — none of them actually scan the printed sheet image the way a
    presser's phone would. The gate caught it only because the smoke check was followed
    literally: "compose a gang sheet, and the header plus transfer QRs decode."

## What the team learned
- Finding A is the sharpest lesson of this wave: an automated suite that never looks at
  the *actual rendered artifact* (here, scanning the printed QR image, not just checking
  the compose call succeeded) can stay green while a shipped, load-bearing feature quietly
  stops working with no error anywhere. A passing API test is not the same claim as "the
  QR code scans."
- Both findings were deterministic and precisely located (one missing field, one
  silent-drop path) — the gate didn't need to retry either one to be confident, and
  recommended a narrow re-run (imaging pytest plus one more compose-and-scan pass) rather
  than a full re-gate once fixed.

## Files to look at
- `invai-imaging/app/pdf_input.py`, `app/vips.py` — PDF/SVG input (T-9-1).
- `invai-imaging/app/compose.py` — the header QR path behind finding A (T-9-2).
- `invai-imaging/app/pdf.py` — long-PDF handling without `/UserUnit` (T-9-3).
- `invai-imaging/app/qa.py` (or wherever `qa.check()` lives) — finding B's missing
  `target_dpi` (T-9-1/T-9-2 boundary).
- `invai-imaging/app/render.py`, `app/fonts.py` — personalization (T-9-4).
- `invai-imaging/app/main.py` (auth dependency, concurrency limiter) — T-9-5.
- `invai-docs/waves/9/gate.md` — both findings in full, and the first fully-green
  three-suite run.
