# T-27-2: Imaging scene base, scene composite and design-lock checks

| Field | Value |
|---|---|
| Wave | 27 |
| Scope ref | `product/scope.md#listing-photos` (SCR-008, phase B) |
| Spec | `specs/listing-photos.md` |
| Owner | imaging-engineer |
| Reviewer | reviewer (fable) |
| Co-reviewers | security-reviewer (opus, files: model output is untrusted bytes) |
| Risk flags | files, marketplace-policy |
| Model | opus |

## Read first
- `.claude/agents/imaging-engineer.md`, `imaging-change-with-budget`; ADR 0023; `waves/27/wave.md` "Agreed interfaces"; your wave 26 work (`/photo/render`, templates, presets, XMP).

## Owned paths (edit)
- `invai-imaging/**` (not `Dockerfile`). Add `/photo/scene-composite` and `/photo/scene-base` to `HEAVY_PATHS` (`app/guard.py`). A new dependency (for example scikit-image for SSIM) needs a reason in the report; prefer a small SSIM in numpy/pyvips if it stays exact enough.

## Acceptance criteria
1. `/photo/scene-base` renders the garment template (`on_model_white` or a new `lifestyle_base`: garment on a neutral figure, room for a background) at `size_px` on the blank hex, and an edit mask PNG in the provider's convention (transparent = editable; the garment's print area and a small margin opaque = protected). Returns `print_box_px` in base-image pixels.
2. `/photo/scene-composite` loads the generated scene (pixel caps and format checks apply; non-image or oversized → 400), then:
   - **Check 1, garment outline aligned (plan review item 8):** registers the generated scene to the base (the provider may re-render the whole frame and returns 1024², 1536×1024 or 1024×1536), then compares an edge map in a ring around the print box; below the threshold → `passes=false`, failure `region_changed`, no composite saved. Then the base's blank print-box pixels are restored into the registered scene before compositing.
   - Upscales the provider-size scene to the preset size (documented method; Etsy ≥ 2000 px).
   - Composites the design at its real print size into the print box with displacement and shading taken from the generated scene's luminance in that region (folds and light follow the scene), white-underbase rule as in wave 26.
   - **Check 2, design lock:** de-shades the printed region and compares it to the source design scaled to the box (SSIM or a documented perceptual metric); `design_lock_score` below the threshold → failure `design_drift`, output not saved.
   - Applies the preset (size, format, background rules; lifestyle images are never `amazon_main`) and writes `xmp_subjects` as XMP `dc:subject`.
3. Thresholds are constants with a comment on how they were chosen; tests show: an unchanged scene passes both checks; a slightly perturbed whole frame (like the mock does) still passes; a shifted or reshaped garment fails check 1; a composite with a swapped/recolored design fails check 2; shading still passes check 2.
4. Same safety as wave 26: shared secret, company-prefix keys, pixel caps. Budgets reported: composite time at 2048 px, peak RSS.
5. Look at the output: base, mask and composite for a tee on model and a hoodie, light and dark blank; paths in the report.

## Verification
- `cd invai-imaging && uv run ruff check . && uv run pytest -q 2>&1 | tail -n 40`; curl both routes on `:8141` (record PID, stop it).

## Out of scope
- Calling any image model (T-27-1 / T-27-3). Backend client functions (T-27-3 has the grant).

## Commit and report
- Commit own paths, co-author line; don't push. Report `invai-docs/waves/27/reports/T-27-2.md` (≤ 60 lines); reply ≤ 8 lines.
