# T-9-1: PDF and SVG input at target DPI — report

Repo: `invai-imaging`. Commit: `bbb85a3` (on `main`, not pushed — pushing is the tech
lead's/gate's job per `agent-brief.md`).

## What changed

- **`app/vips.py`**: `load(path, access="random", target_dpi: float | None = None)`. New,
  additive, defaults to `None` — every existing caller (`compose.py`, `render.py`, `qa.py`,
  `mockups.py`) is unaffected until it opts in.
  - Added `_sniff(path)`: reads the first 256 bytes and returns `"pdf"` / `"svg"` / `None` by
    magic bytes (`%PDF-`, `<?xml`/`<svg` after stripping BOM/whitespace). Required because
    `main.py`'s `_download()` writes to an extensionless temp path (`tmp / "input"`), so the
    file suffix isn't available to dispatch on.
  - `kind == "svg"` and `target_dpi` set → `pyvips.Image.svgload(path, scale=target_dpi/72)`.
  - `kind == "pdf"` → routed to the new `app/pdf_input.py::rasterize_pdf`; raises `ImageError`
    if `target_dpi` wasn't given (PDF has no sane "native" raster size to fall back to).
  - Everything else (including SVG with `target_dpi=None`) → unchanged
    `pyvips.Image.new_from_file`.

- **New `app/pdf_input.py`**: `rasterize_pdf(path, dpi) -> pyvips.Image`. Opens page 1 with
  `pypdfium2.PdfDocument`, rejects (`ImageError`) anything with `len(doc) != 1` — art uploads
  are single-page by contract — renders at `scale = dpi/72` with a transparent fill
  (`(255,255,255,0)`), swaps pdfium's native BGRA buffer to RGBA (confirmed live: `bitmap.mode
  == "BGRA"`), loads it into pyvips via `new_from_memory`, then `.copy_memory()` so the image
  is detached from the Python `bytes` buffer before it goes out of scope.

- **`pyproject.toml` / `uv.lock`**: added `pypdfium2>=5.13.0` (installed as `5.13.0`), per the
  tech lead's wave-9 grant (`uv add pypdfium2` in invai-imaging). No Dockerfile change — it's a
  pip-only wheel bundling prebuilt pdfium, no system Poppler needed.

- **New `tests/test_pdf_svg_input.py`**: 8 tests. SVG and PDF two-tone fixtures (2in × 1in,
  red/green halves) at 150 and 300 DPI, asserting `(width_px, height_px) ==
  round(size_in * dpi)` and a fixed `sha256` of the decoded raw RGBA pixels (`to_srgba(img)
  .write_to_memory()`) — not the compressed file, per the card's testability note. Also:
  `load()` without `target_dpi` on an SVG matches plain `new_from_file` (backward-compat
  contract check), PDF without `target_dpi` raises `ImageError`, a 2-page PDF is rejected
  (`"single-page"`), and a corrupt PDF raises `ImageError` (`"unreadable pdf"`).

## Rasterizer decision (confirmed, not from memory)

Same as the card/wave.md already recorded, reconfirmed live in this environment:
`hasattr(pyvips.Image, "pdfload")` → `False` on the installed `pyvips[binary]==3.2.0` /
libvips 8.18.6. `pypdfium2` imports with a plain `uv add` on this macOS arm64 box, no system
packages. **No reject-PDF-at-upload fallback needed** — pypdfium2 works, so that branch of
AC2 doesn't apply.

## A bug found along the way, not in the card/wave docs

`pyvips.Image.svgload(path, dpi=X)` is **not** what you want for physically-sized SVGs.
Checked live: an SVG with `width="10in" height="5in"` (with or without a `viewBox`), loaded
with `dpi=300`, comes out **12,500×6,250px**, not the expected 3,000×1,500 — librsvg applies
the DPI factor once converting `"10in"` to user units, then again as an overall render scale
(quadratic: `size_in * dpi² / 72`). `scale=dpi/72` applies it exactly once and is correct for
both physical-unit and unitless/`viewBox`-only SVGs (verified both cases directly). `vips.py`
uses `scale=`, not `dpi=`, with a comment recording the numbers. This directly matters for AC1
("a 10in SVG at 300 DPI is 3,000px wide") — a naive `dpi=` implementation would have silently
shipped the wrong (4×) size for exactly that acceptance criterion.

## Verification

- `uv run pytest`: 38 passed (30 pre-existing + 8 new), no regressions.
- `uv run ruff check .` and `uv run ruff format --check .`: clean on all files I touched. (A
  pre-existing, unrelated `ruff format` diff exists in `app/labels.py` — not mine, left alone.)
- Live check on port 8190 (`STORAGE=local`): started the service, uploaded a PNG to local
  storage, called `POST /qa/check` — `200` with correct dimensions/DPI, confirming the changed
  `load()` signature doesn't break existing callers. Server stopped and temp storage dir
  removed afterward. No end-to-end SVG/PDF HTTP check was possible yet: no endpoint accepts
  `target_dpi` over HTTP until T-9-2/T-9-4 wire it in their own files, which is by design (my
  card owns only the `load()` signature and `pdf_input.py`).

## For T-9-2 / T-9-4

Call `load(src, target_dpi=<dpi>)` from your own files — no changes needed to `vips.py` or
`pdf_input.py`. `target_dpi` works uniformly for SVG and PDF sources; PNG/JPEG/etc. ignore it
(unchanged path). No grants used or needed outside `app/vips.py`, new `app/pdf_input.py`,
`pyproject.toml`, `uv.lock`.
