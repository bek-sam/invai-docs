# Wave 9 plan review — architect, round 1

Scope: read-only on code (`invai-imaging/app/**`, `invai-backend/src/integrations/imaging/client.ts`, contracts schemas, the imaging Dockerfile). No DB touched, no code committed — only `invai-docs/waves/9/**` changes, applied directly to `wave.md` and the five card files.

## 1. File split across the 5 cards
All five cards live in `invai-imaging`, and several of the "core" files (`main.py`, `vips.py`) are shared choke points, so a naive "one card = one file" split doesn't work. Read every touched file (`vips.py`, `compose.py`, `pdf.py`, `render.py`, `fonts.py`, `qa.py`, `nesting.py`, `storage.py`, `main.py`, `config.py`) before deciding. Findings:

- `app/vips.py`'s `load()` is the single choke point for all raster input (compose designs, personalization backgrounds, QA checks). T-9-1's DPI fix has to live there, and T-9-2 (`compose.py`) / T-9-4 (`render.py`) each need a one-line call-site change to use it. That's a real cross-card dependency, but it's **additive and one-directional** — T-9-1 adds an optional kwarg, the other two just start passing it. Sequencing T-9-1 first removes the risk without needing a shared-file grant.
- `app/pdf.py` currently only has the *write* path (`write_image_pdf`, used by `compose.py`). T-9-1 needs a *read* path (PDF→raster). Putting that in a **new** `app/pdf_input.py` instead of extending `pdf.py` keeps T-9-1 and T-9-3 (which edits `write_image_pdf`'s `/UserUnit` logic) on entirely disjoint files, so they don't need to be sequenced relative to each other at all.
- `app/main.py` is touched by four of the five cards, but each touches a **different Pydantic model class** (`ComposeRequest` for T-9-2, `NestRequest`/`ComposeRequest.max_length_in` for T-9-3, `SlotModel`/`TemplateModel` for T-9-4, and the whole-app auth/concurrency layer for T-9-5). Per `team/agent-brief.md`'s hard rule ("stage only your own hunks... check `git diff --cached`"), disjoint classes in one file is an acceptable parallel edit, not a collision — I called this out explicitly in `wave.md` and each card rather than inventing a `main.py`-splitting scheme nobody asked for.
- Net result: **T-9-1 solo first** (defines the shared interface), **T-9-2/T-9-3/T-9-4 in parallel** (disjoint primary files, disjoint `main.py` classes), **T-9-5 solo last** (wraps the whole app; benefits from a stable, already-landed endpoint surface, and is the highest-risk/opus card — smallest possible diff window is the right trade for a security review).

## 2. PDF rasterizer path (T-9-1) — checked live, not from memory
```
$ uv run python -c "import pyvips; print(hasattr(pyvips.Image, 'pdfload'))"
False   # pyvips 3.2.0 / libvips 8.18.6
```
Confirms B-78 exactly. Then checked both alternatives for real:
- `pip install pypdfium2` succeeds on this machine (macOS arm64) with no system Poppler — pypdfium2 ships its own prebuilt binary in the wheel.
- `pip download --platform manylinux2014_x86_64 --python-version 3.13 pypdfium2` succeeds too (`pypdfium2-5.13.0-py3-none-manylinux_2_17_...whl`), and manylinux2014's glibc floor (2.17) is far below Debian 12/13's (the imaging Dockerfile's `python:3.13-slim` base), so it'll run in the Docker image with **no Dockerfile change**.
- Poppler-based options (`pdf2image`, `python-poppler`) both wrap the `poppler-utils` system binary, which isn't installed in the slim image or on a bare macOS dev box — they'd need an `apt-get` line plus a Homebrew step for dev parity, for no functional gain over pypdfium2 here.
- **Decision: pypdfium2.** Full rationale and the exact new-module shape are in `wave.md` and `T-9-1-pdf-svg.md`.

## 3. T-9-3: cap vs split
**Cap**, scoped to `format: "pdf"` only (PNG has no page-size concept, so B-80 doesn't apply to it). Reasoning is in `wave.md`/`T-9-3-long-pdf.md`: it's a smaller diff (removes `/UserUnit` entirely instead of special-casing it — 200in×72pt is exactly the existing `MAX_PAGE_PT`), it matches how DTF RIPs (CADlink) actually consume a job (one continuous image per barcode lookup, not a multi-page bundle needing operator re-assembly), and it matches the segment this wave is actually shipping to (`scope.md`: pilots start mid; large-shop, high-volume workflows most likely to hit >200in are gated behind `scale-test` anyway). Enforce it at `SheetSpec` save (contracts), not just at compose time, so a shop finds out before a job is queued.

## 4. Contract changes
Exact diffs are written into `wave.md` (§Plan review r1) and cross-referenced from `T-9-2`/`T-9-3`/`T-9-4`. Two things worth flagging beyond the diffs themselves:
- `TEMPLATE_FONTS` **already exists** in `invai-contracts/src/schemas/personalization.ts` but `TemplateSlot.fontFamily` was never switched from `z.string()` to `z.enum(TEMPLATE_FONTS)` — B-81 isn't "add an enum," it's "wire up the one that's already there," and the real bug is `app/fonts.py:31-33`'s silent fallback, which the contract enum alone doesn't fix.
- `invai-backend/src/integrations/imaging/client.ts` is a hand-kept duplicate of the imaging response/request shapes (confirmed by reading it — it re-declares `TemplateSlot`, `ComposePlacement`, etc. in zod, separately from `invai-contracts`), and it's flagged as a known issue in the audit (B-104). None of the five cards' owned paths include it, so any contract change here silently drifts unless a card explicitly touches it. I added narrow grants for T-9-4 (font/slot fields) and T-9-5 (retry-on-429) rather than leaving it as a silent gap.

## 5. Two scope gaps found outside invai-imaging (flagged, not routed around)
- T-9-2 AC2's "file name includes the sheet id and order numbers" evidence (`sheets.ts:559-561`) points at `invai-backend/src/lib/s3.ts`'s `objectKey()`, which is explicitly documented as opaque/random by design ("keys never contain user input") and isn't in any wave-9 card's owned paths. Rather than granting a card into a security-relevant backend invariant, the fix moves entirely inside `invai-imaging`: a `filename_hint` on `ComposeRequest` set as the S3 `ContentDisposition` on upload. This satisfies the actual need (what a vendor/RIP operator sees when they save the file) without touching the key scheme.
- T-9-5 AC1's "the backend client retries" needs an edit in `invai-backend/src/integrations/imaging/client.ts`, also outside invai-imaging. Given as a single-function narrow grant (`call()`, one retry branch) rather than a 6th card, since the wave cap is 5.

## 6. Acceptance-criteria testability
Went through all five cards' ACs against what's actually testable with the current code:
- T-9-1 AC3's "visual checksum" is unspecified; recommended hashing decoded raw pixels (rendering is deterministic here — no anti-aliasing randomness across runs) rather than the compressed file.
- T-9-2 AC1's "fails loudly" needs a concrete boundary (module size vs. label-strip height at a given DPI) or the test can't assert exactly when it should trip.
- T-9-4 AC1 introduces a second shrink floor (`minFontSizePt`) alongside the existing 60%-of-size default and doesn't say which wins — recommended the more generous of the two.
- T-9-5 AC2 is currently untestable as written for two of its four bounds: `ComposePlacementModel` has no list-length cap and `width_in`/`sheet_width_in` have no `le=60` in `app/main.py` today (confirmed by reading it). Flagged as "add the bound, then write the test," not a plan-only fix.

No DB access, no pushes, no code edits made — everything above is applied only to `invai-docs/waves/9/**`.
