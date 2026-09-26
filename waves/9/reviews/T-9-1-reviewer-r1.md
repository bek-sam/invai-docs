# Review of T-9-1 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: imaging-engineer on Sonnet
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `uv run ruff check .` (invai-imaging) | All checks passed! |
| `uv run pytest` (invai-imaging) | 38 passed (30 pre-existing + 8 new), 0 failed |
| `git -C invai-imaging show bbb85a3 --stat` | 5 files: `app/pdf_input.py` (new), `app/vips.py`, `pyproject.toml`, `uv.lock`, `tests/test_pdf_svg_input.py` — matches owned paths exactly |
| `git -C invai-imaging diff origin/main..bbb85a3 --stat` | Confirms bbb85a3 not pushed (local `main` 3 ahead of `origin/main`); only T-9-1's files in its own commit |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-imaging bbb85a3^` | "Result: no hits" (0 removed assertions, 5 added, no skips/mocks/snapshot changes) |
| Archived `origin/main`'s parent tree, copied `tests/test_pdf_svg_input.py` in, `uv run pytest tests/test_pdf_svg_input.py` | Collection error: `ModuleNotFoundError: No module named 'app.pdf_input'` — the new tests are real, they fail without the fix |
| Own script: `pyvips.Image.svgload(path, scale=dpi/72)` vs `dpi=dpi` on a 10in×5in physical-unit SVG, at 150/300 DPI | `scale=`: 1500×750 and 3000×1500 (correct). `dpi=` kwarg: 3125×1563 and 12500×6250 (quadratic bug, confirms report's claim) |
| Own script: same `scale=` load against a viewBox-only (no width/height) SVG and a `width="100%" height="100%"` (percent) SVG sharing the same `viewBox="0 0 1000 500"` | Both produce **identical** dimensions at each DPI (2083×1042 @150, 4167×2083 @300) — percent-sized resolves against the viewBox, same single-DPI-factor behavior as viewBox-only; no double-application for either |
| Own script: `pypdfium2.PdfDocument` + `page.render(scale=dpi/72)` on a synthetic 5000in×5000in page | Would request a ~1,500,000×1,500,000px bitmap at 300 DPI — no cap anywhere in `pdf_input.py`/`vips.py`/`main.py` stops this before rendering |
| `cat invai-imaging/Dockerfile` | `FROM python:3.13-slim` (glibc/Debian), no Poppler installed, no change made |
| `grep pypdfium2 uv.lock` | Resolved wheels include `pypdfium2-5.13.0-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl` and an aarch64 manylinux wheel — both ABI-compatible with `python:3.13-slim`'s glibc; matches the report's claim, no Dockerfile change needed |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. SVG rasterized at target print size × DPI (designs and template backgrounds) | Yes | `test_svg_rasterized_at_target_dpi` passes; own script confirms `scale=dpi/72` gives the exact expected pixel size (3000×1500 for a 10in SVG at 300 DPI) and is correct across physical-unit, viewBox-only and percent-sized SVGs (see evidence row above) |
| 2. PDF artwork rasterized at target DPI via a no-GPU rasterizer available in the Dockerfile | Yes | `pypdfium2` confirmed installed via pip-only wheel (`uv.lock`), manylinux wheel present for the Docker base, no Dockerfile change; `test_pdf_rasterized_at_target_dpi` passes and matches expected pixel dims + a fixed pixel digest |
| 3. SVG and PDF fixtures at 150/300 DPI checking pixel dims and a visual checksum of decoded raw pixels | Yes | `tests/test_pdf_svg_input.py` — 8 tests, dims via `round(size_in*dpi)`, digest via `sha256(to_srgba(img).write_to_memory())`, not the compressed file; confirmed these fail on the pre-fix tree (`ModuleNotFoundError`) |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`app/vips.py`, new `app/pdf_input.py`, `pyproject.toml`/`uv.lock`, its own new test file — matches the card's `Owns:` line exactly)
- [x] Nothing outside scope (no changes to `app/main.py`, `compose.py`, `render.py`, etc.; `T-9-2`/`T-9-4` wiring `load(target_dpi=...)` into their own files is explicitly left for them per the report and card)
- [x] Tests exercise the behavior, and none were weakened — scan script: no hits; new tests independently confirmed to fail pre-fix
- [x] Tenancy / idempotency / money-in-cents / en+es text: n/a, this card touches only a pure image-loading utility with no tenant, money or user-text surface
- [x] Decisions recorded where needed — rasterizer choice (pypdfium2 over poppler) and the `scale=` vs `dpi=` SVG bug are both recorded in the card, `wave.md` and the report, and reproduced live in this review

## Optional notes (not blocking)
1. **Cross-card flag for T-9-5, not a block on this card:** `app/pdf_input.py::rasterize_pdf` has no pixel-budget cap — a PDF with an oversized `MediaBox` (e.g. 5000in × 5000in) would ask pdfium to render a multi-hundred-megapixel-to-gigapixel bitmap before any check runs. This is currently unreachable (no HTTP endpoint passes `target_dpi` yet — T-9-2/T-9-4 land that), so it isn't a live risk today, and the wave's own plan review explicitly assigns "a pixel cap on decode" to T-9-5 AC2, sequenced last on purpose. But T-9-5 AC2 phrases its cap as "the libvips limit" — PDF input never touches libvips' decode path (it goes straight from `pdfium.PdfDocument.render()` to an in-memory buffer), so a libvips-side pixel limit alone will not catch an oversized PDF page. T-9-5 (or its architect co-review) should add an explicit check on `page.get_size() × (dpi/72)` before calling `render()`, not just rely on a generic libvips cap.
2. `rasterize_pdf`'s stride-padding fallback branch (`img.crop(...)` when `stride != w * n`) wasn't exercised by any fixture I could construct on this platform (pdfium's buffer was tightly packed for every width I tried, including odd inch fractions); logic reads correctly by inspection but is currently untested. Low priority given libvips' own header check (`_ = img.width`) would surface any dimension mismatch immediately.
3. Non-integer-inch PDF pages (e.g. 1.01in wide) showed a 1px pdfium-side rounding/anti-aliasing artifact at the exact edge column in my own probing — appears to be inherent to pdfium's own rasterizer, not something this diff introduces, and the card's fixtures use exact-inch dimensions that don't hit it. Worth a note if a future card adds fractional-inch DTF designs.
