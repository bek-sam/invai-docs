# T-9-1: PDF and SVG input at target DPI (B-78)
Evidence: §A-INF B-1, B-2 (`app/vips.py:25-32`, no `pdfload`, SVG loaded at 72 DPI).
## Acceptance criteria
1. **SVG:** rasterized at (target print size × sheet DPI), not at 72 DPI. This applies to designs and to template backgrounds. A 10 in SVG at 300 DPI is 3,000 px wide.
2. **PDF artwork:** rasterized at the target DPI (use a rasterizer available without a GPU; check whether libvips in the installed wheel supports `pdfload`, otherwise use pdfium or poppler through a pip wheel, which the Dockerfile must support). If that isn't feasible, reject PDF at upload in the backend with a clear message. Record the decision.
3. **Tests:** SVG and PDF fixtures at 150 and 300 DPI, checking pixel dimensions and a visual checksum (hash decoded raw pixels, not the compressed file — rendering is deterministic, so a fixed digest per fixture/DPI is a valid assertion).

## Plan review r1 — files, sequencing, decision
Runs **solo, first** (see `wave.md` §Plan review r1) — T-9-2/T-9-4 call sites depend on the `load()` signature this card adds, so it lands before the 3-way parallel batch.

**Owns:** `app/vips.py` (`load()` gets an additive `target_dpi: float | None = None` param; SVG sources pass it through as the loader's `dpi=` option, PDF sources route to the new module below), new `app/pdf_input.py`, `pyproject.toml`/`uv.lock`. No grants needed elsewhere — T-9-2 and T-9-4 add their own one-line `load(src, target_dpi=...)` call in their own files once this lands.

**Rasterizer decision (checked live, not from memory):**
- Installed wheel `pyvips[binary]==3.2.0` / libvips 8.18.6 has **no `pdfload`** — confirmed with `hasattr(pyvips.Image, "pdfload")` → `False`.
- **pypdfium2** installs and imports on macOS arm64 dev with plain `pip install` (no system Poppler), and PyPI has a `manylinux_2_17_x86_64` wheel (verified downloadable) that's ABI-compatible with the Dockerfile's `python:3.13-slim` base — **no Dockerfile change**.
- poppler wheels (`pdf2image`/`python-poppler`) need the `poppler-utils` system binary, absent from the slim image and from a bare macOS dev box — more setup for the same result.
- **Use pypdfium2.** New `app/pdf_input.py::rasterize_pdf(path, dpi) -> pyvips.Image` (page 1 via `pdfium.PdfDocument`, fed into `pyvips.Image.new_from_buffer`). Reject multi-page PDFs with a 422 — art uploads are single-page.
