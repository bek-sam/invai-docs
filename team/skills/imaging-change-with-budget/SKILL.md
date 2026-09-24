---
name: imaging-change-with-budget
description: Change invai-imaging (nesting, gang-sheet compose, PDF, print-file QA, personalization, mockups, labels) while holding exact physical size, scannable QR labels, peak RSS, a decode pixel cap and the DTF defaults (0.25 in gap and margin, 150 DPI floor). Use for any change under invai-imaging/app, "gang sheet", "nest", "compose", "DPI", "QR label", "render".
---

# Imaging change with budget

A change to the imaging service that keeps inches exact, every QR scannable, memory flat on a 22 × 240 in sheet, and what the printer receives unchanged unless the card says so.

## When to use
- Any edit in `invai-imaging/app/**` (owner: imaging-engineer).
- A response-shape change also touches `invai-backend/src/integrations/imaging/client.ts` (integrations-engineer): coordinate through the tech lead.

## Budgets (current numbers from `invai-imaging/README.md`, Apple Silicon)
| Output (22 × 239.85 in, 300 DPI, 93 designs) | Time | Peak RSS |
|---|---|---|
| PNG + preview | 4.1 s | 440 MB |
| PNG + PDF + preview | 10.2 s | 495 MB |
- Idle process about 75 MB. Memory must stay **flat in sheet length**. Fail the change on a regression over 25% in time or RSS (research 12 §3.9).
- Research 11 §6.4 plans for about 1 GB per 240 in compose on the 8 GB task (the runbook's `TMP_DIR` row also says a 240" sheet needs about 1 GB of scratch disk); there is **no compose concurrency limit yet** (research 11 G15, backlog B-19). Don't add work that assumes one compose at a time.

## DTF defaults (research 10 §8, keep them)
- Gap between designs **0.25 in**, edge margin **0.25 in**: `NestRequest` defaults `spacing_in=0.25`, `margin_in=0.25` in `app/main.py`, matching `DEFAULT_SHEET_SPEC` in `invai-contracts/src/schemas/vendors.ts` and the backend vendor spec. Contour-cut vendors need 0.5 in: that's a vendor spec value, never a new hard-coded default.
- DPI: **150 is the hard floor** (`DPI_ERROR = 150` in `app/qa.py`), 300 the target (`DPI_WARN`). Output is transparent RGBA PNG with 300 DPI metadata.
- `label_height_in` (default 0.35) must be identical between `/nest` and `/compose`.
- Film width and max length come from the vendor spec (22 in and 240 in are defaults only). Sheet file names and barcodes must carry our sheet id (CADlink looks jobs up by name or barcode).

## Steps
1. **Read** `invai-imaging/README.md` (endpoints, "Details the caller should know", "Performance"), the module you change and its tests (`tests/test_nesting.py`, `test_compose.py`, `test_qa.py`, `test_render.py`, `test_api.py`).
2. **Write the test first** at the lowest layer: a pure function in `app/nesting.py` or `app/qa.py` beats an API test.
3. **Dimension tests.** For every output, assert pixel size equals `round(inches × dpi)` and the DPI metadata (`round(xres × 25.4) == dpi`), and for PDFs the page size in points / 72 == inches (pages over 200 in use `/UserUnit`; see `test_long_sheet_pdf_uses_user_unit`). Sizes are never rounded to whole inches anywhere.
4. **QR decode test.** Keep `test_compose.py`'s check that decodes every label QR with `zxingcpp.read_barcodes` and gets exactly the set of `transfer_id`s. Any change to label layout, QR size, quiet zone or compose must keep it green. Add a case for your change (rotated design, narrow design, REPRINT line).
5. **Nesting properties** (Hypothesis is the target, research 12 §3.2; not installed yet, add it to the `dev` group if the card allows): no overlaps including the gap, inside width and margins, each copy placed exactly once or reported, utilization ≤ 1, deterministic output.
6. **Pixel cap and format allowlist** (research 12 §1.6, G4): before decoding untrusted input, read the header and reject anything over about 22 × 240 in at 300 DPI × 1.2 (≈ 570 million pixels); allow only PNG, JPEG, WebP, TIFF (SVG/PDF only where a feature needs them) using `pyvips.block_untrusted_set(True)` or the specific loader. `app/vips.py` `load()` calls `new_from_file` on anything today. Treat Pillow `DecompressionBombWarning` as an error wherever Pillow opens user data.
7. **Stay streaming.** Never load a full sheet into Pillow. Big images go through pyvips with sequential access (`load(path, access="sequential")` where possible), the sheet as a lazy graph streamed to `pngsave`, the PDF streamed in strips (`app/pdf.py`).
8. **Measure peak RSS and time** for compose or nest changes on a full-length sheet, before and after, on the same machine:
   ```
   cd invai-imaging
   /usr/bin/time -l uv run pytest tests/test_compose.py -k <your_full_sheet_case> 2>&1 | grep -E "maximum resident|real"
   ```
   (macOS `time -l` reports "maximum resident set size" in bytes.) A reusable benchmark script is to be created (`invai-imaging/bench/`, research 12 §3.9). Record the numbers in the README "Performance" table.
9. **Deterministic outputs.** Output keys come from the caller; the same input must produce the same file so a retried render overwrites (research 11 §6.4).
10. **Run for real** against MinIO: `uv run uvicorn app.main:app --port 8000`, call the endpoint (curl or the backend's sheet build), download the PNG and look at it: art inside boxes, labels readable, nothing clipped. For golden-path changes, rebuild a sheet on the seed and check film use stays ≥ 80% (`E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts` in `invai-web`).
11. **Check:** `uv run ruff check . && uv run ruff format --check . && uv run pytest`.

## Rules (MUST / MUST NOT)
- MUST keep inches in = inches out at the requested DPI; MUST NOT hard-code 22 in, 240 in or 300 DPI outside request defaults.
- MUST keep the QR encoding exactly `transfer_id`, opaque white with a quiet zone.
- MUST keep errors as `422 {"detail": ...}`, and an unreadable existing key as a 200 `unreadable` issue in QA.
- MUST keep the HTTP API stable: optional fields only, unless a coordinated card says otherwise.
- MUST escalate (`escalate-to-owner`) changes a vendor would notice on the printer: format, color profile, page size behaviour.
- If an AI-generated person is ever composited into a mockup, write the XMP `contains-synthetic-performer` tag for Amazon (research 10 §4).

## Done when
- Dimension and QR-decode tests cover the change; ruff and pytest pass.
- Peak RSS and time before/after are in the report and the README (for compose or nest changes), within budget.
- The output PNG was opened and looked at; the golden path still builds a sheet at ≥ 80% film use.

## References
- `invai-imaging/README.md`, `app/{nesting,compose,pdf,qa,vips,main}.py`, `tests/`
- `invai-docs/research/10-marketplace-engineering-rules.md` §8 (DTF practices), §9 item 30
- `invai-docs/research/11-platform-scale-playbook.md` §6.4; `12-security-quality-playbook.md` §1.6, §3.2, §3.9
- `invai-docs/waves/backlog.md` B-19, B-35
- Related: `scale-test`, `root-cause-bug`
