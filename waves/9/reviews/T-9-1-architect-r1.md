# Review of T-9-1 (round 1)

- Reviewer: architect on Sonnet 5
- Author: imaging-engineer on Sonnet
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `uv run ruff check .` (invai-imaging) | All checks passed! |
| `uv run pytest` (invai-imaging) | 38 passed, 0 failed |
| `git -C invai-imaging show bbb85a3 --stat` | Only `app/pdf_input.py` (new), `app/vips.py`, `pyproject.toml`, `uv.lock`, `tests/test_pdf_svg_input.py` — matches the card's owned-paths grant (`app/vips.py`, new `app/pdf_input.py`, `pyproject.toml`/`uv.lock`), no touch to `app/main.py` or any file another wave-9 card owns |
| Own script: `load()`'s new `target_dpi` param on physical-unit, viewBox-only and percent-sized (`width="100%" height="100%"` + `viewBox`) SVGs, at 150/300 DPI | `scale=target_dpi/72` gives the exact expected size for physical units (3000×1500 for a 10in SVG at 300 DPI) and identical, single-factor scaling for viewBox-only vs. percent-sized (both 4167×2083 at 300 DPI off the same `viewBox="0 0 1000 500"`) — no quadratic blow-up in any of the three cases |
| Own script: `svgload(..., dpi=300)` on the same physical-unit SVG | 12500×6250 instead of 3000×1500 — reproduces the exact bug the author reports librsvg has with the `dpi=` kwarg; confirms the decision to use `scale=` instead was necessary, not cosmetic |
| Own script: 5000in×5000in synthetic PDF page through `pypdfium2.PdfDocument`/`page.render(scale=dpi/72)` math | Requests ≈1.5M×1.5M px at 300 DPI; no cap exists anywhere on the path from `load(target_dpi=...)` → `rasterize_pdf` → `page.render()` |
| `cat invai-imaging/Dockerfile`; `grep pypdfium2 invai-imaging/uv.lock` | Base is `python:3.13-slim` (glibc, no Poppler); `uv.lock` resolved `pypdfium2-5.13.0-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl` (and an aarch64 manylinux wheel) — both are glibc-compatible with the slim base, so "works in the Linux Docker image, no Dockerfile change" is a verified fact, not an assumption |
| Read `wave.md` §Plan review r1, §Decision: PDF rasterizer path | Confirms this card's sequencing ("solo, first," T-9-2/T-9-4 depend on the `load()` signature) and the pixel-cap/format-bounds work is explicitly T-9-5 AC2's job, deliberately deferred until the parallel batch's endpoint surface is stable |
| Archived pre-fix tree + copied in the new test file, ran under it | `ModuleNotFoundError: No module named 'app.pdf_input'` — new tests are not tautological |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. SVG rasterized at (target print size × DPI), correct for designs and template backgrounds | Yes | `load()` routes any SVG with `target_dpi` set through `svgload(scale=target_dpi/72)`; verified correct and equivalent across physical-unit, viewBox-only, and percent-sized inputs |
| 2. PDF rasterized at target DPI via a no-GPU rasterizer the Dockerfile supports | Yes | `pypdfium2` confirmed pip-installable with a manylinux wheel matching the Dockerfile's base image; the "reject PDF at upload" fallback in the AC is correctly not exercised since pypdfium2 works |
| 3. Fixtures at 150/300 DPI, pixel dims + pixel-decode checksum | Yes | 8 new tests in `tests/test_pdf_svg_input.py`, confirmed to fail pre-fix |

## Blocking findings
None.

## Architectural notes
1. **Interface design is sound for the sequencing this wave chose.** `target_dpi: float | None = None` is additive and every existing caller of `load()` (`compose.py`, `render.py`, `qa.py`, `mockups.py`) is provably unaffected (there's a dedicated regression test for this: `test_svg_without_target_dpi_is_unchanged`). This is exactly the contract T-9-2/T-9-4 were told to depend on in `wave.md`, and it holds.
2. **Content-sniffing by magic bytes (`_sniff`) instead of trusting the file suffix is the right call** given `main.py`'s `_download()` writes to an extensionless temp path — there is no suffix to dispatch on, so this isn't optional complexity, it's required by how the rest of the app already works.
3. **Memory handling in `rasterize_pdf` is correct for the happy path**: `bitmap.close()` before returning, `img.copy_memory()` detaches the vips image from the Python `bytes` buffer before it's freed — this avoids a use-after-free/dangling-buffer class of bug that's easy to get wrong when bridging a C buffer into pyvips via `new_from_memory`.
4. **Pixel-budget gap, correctly scoped out of this card but needs a specific fix in T-9-5, not a generic one.** `rasterize_pdf` has no check on the requested output size before calling `pdfium`'s `page.render()`. Confirmed live that an adversarial PDF page (oversized `MediaBox`) would request a multi-megapixel-to-gigapixel bitmap with nothing stopping it. This is not exploitable yet — no HTTP endpoint passes `target_dpi` until T-9-2/T-9-4 land, and `wave.md`'s plan review explicitly assigns "a pixel cap on decode" to T-9-5 AC2, sequenced last for exactly this reason. But T-9-5 AC2 as written says "the libvips limit" — that phrasing assumes every decode path goes through libvips, and this card just proved one doesn't: PDF input goes `pdfium.PdfDocument → page.render() → new_from_memory`, entirely outside libvips' own decode-time limits. **Recommendation for T-9-5's plan/review:** add an explicit check of `page.get_size() × (dpi/72)` against the pixel budget before calling `render()`, as its own guard, not something a libvips-side cap will incidentally cover. Flagging this now, while the call site is fresh, rather than after T-9-5 lands.
5. **Multi-page rejection is the right contract-level decision, not just an implementation shortcut.** `wave.md`'s "art uploads are single-page by contract" holds up: rejecting with `ImageError` (→422) rather than silently taking page 1 avoids a shop uploading a multi-page proof PDF and getting the wrong page composited without any signal.

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened (scan script: no hits)
- [x] Tenancy / idempotency / money-in-cents / en+es text: n/a (pure image-loading utility, no tenant/money/user-text surface)
- [x] Decisions recorded where needed (rasterizer choice and the `scale=` vs `dpi=` bug are in the card, `wave.md`, and the report, and independently reproduced here)

## Optional notes (not blocking)
Same stride-padding and non-integer-inch-PDF observations as the reviewer's r1 file — see `T-9-1-reviewer-r1.md` for detail; neither is exercised by this card's fixtures and neither is introduced by this diff.
