# Wave 9: imaging for real print shops

- Goal:
  - Shops' real art files (PDF, SVG) print at the right size.
  - Every sheet and transfer is scannable at any DPI.
  - Long sheets print true to size.
  - Personalization covers multi-line, outline and photo slots.
  - The imaging service is safe against huge or hostile inputs.
- Rules: `team/agent-brief.md`. Evidence: `build/audit-2026-09-24.md` §A-INF, part B.

## Cards
| Card | Owner | Co-reviewers | Flags | Model |
|---|---|---|---|---|
| T-9-1 PDF and SVG input at target DPI (B-78) | imaging-engineer | architect | files | sonnet |
| T-9-2 Sheet barcode, scannable QRs, label gap (B-79) | imaging-engineer | qa-engineer | floor-correctness | sonnet |
| T-9-3 Long PDFs without `/UserUnit` (B-80) | imaging-engineer | architect | files | sonnet |
| T-9-4 Personalization upgrades (B-81) | imaging-engineer + web-engineer | product-designer, architect | ui | sonnet |
| T-9-5 Imaging limits and service auth (B-19) | imaging-engineer + platform-sre | security-reviewer | files, auth | opus |

All five cards are in invai-imaging, so the plan review must split files (`vips.py`, `compose.py`, `pdf.py`, `render.py`/`fonts.py`, `main.py`) and sequence where needed. Run 3 at once.

## Plan review r1 (product-manager + architect) — file split, sequencing, decisions
Full rationale: `reviews/plan-product-manager-r1.md`, `reviews/plan-architect-r1.md`.

### Sequencing (5 cards, "run 3 at once")
1. **Solo first: T-9-1.** It defines a new, additive parameter on `app/vips.py`'s `load()` (`target_dpi`) that T-9-2/T-9-4 call sites depend on. Land it before the parallel batch so nobody codes against a moving signature.
2. **Parallel batch (3 at once): T-9-2, T-9-3, T-9-4.** Disjoint primary files (see matrix). Each touches a *different* Pydantic model class inside `app/main.py` — stage only your class's hunk (`git add -p`), and if you land second, rebase past the other's `main.py` diff; no shared lines.
3. **Solo last: T-9-5.** It wraps the app with auth, concurrency limiting, format/pixel bounds and dev-flag gating — do this once the batch's endpoint surface (new fields on `ComposeRequest`/`NestRequest`/`SlotModel`) is stable, so the hardening isn't churned. Opus, highest risk, security co-review — give it the smallest, most isolated diff window.

### File ownership matrix
| Card | Owns (primary) | Narrow grants (single class/field only) | Runs |
|---|---|---|---|
| T-9-1 | `app/vips.py`, new `app/pdf_input.py`, `pyproject.toml`/`uv.lock` (add `pypdfium2`) | — | solo, first |
| T-9-2 | `app/compose.py`, `app/storage.py` (add optional `download_filename` → S3 `ContentDisposition`) | `app/main.py`: `ComposeRequest` class only (add `label_gap_in`, `filename_hint`); `invai-contracts/src/schemas/vendors.ts`: `SheetSpec` (`labelGapIn`) | parallel |
| T-9-3 | `app/pdf.py` | `app/main.py`: `NestRequest`/`ComposeRequest.max_length_in` bound only; `invai-contracts/src/schemas/vendors.ts`: `SheetSpec` (`.refine` on `maxLengthIn`) | parallel |
| T-9-4 | `app/render.py`, `app/fonts.py`, `invai-web` template editor | `app/main.py`: `SlotModel`/`TemplateModel` classes only; `invai-contracts/src/schemas/personalization.ts`; `invai-backend/src/integrations/imaging/client.ts` (mirror the same fields — see gap below) | parallel |
| T-9-5 | `app/main.py` (auth dependency, concurrency limiter, bounds, dev-flag gating), `app/config.py`, `Dockerfile` (HEALTHCHECK) | `invai-backend/src/integrations/imaging/client.ts`: `call()` only (429 + `Retry-After` retry — see gap below) | solo, last |

**Scope gaps found (not covered by any card's owned paths — flag to tech lead, don't route around):**
- T-9-2 AC2 ("file name includes the sheet id and order numbers") can't be done by changing the S3 object key: `invai-backend/src/lib/s3.ts:51` deliberately keeps keys opaque/random ("keys never contain user input"), and that file isn't in any imaging card. **Fix stays inside invai-imaging instead:** add `filename_hint` to `ComposeRequest`, pass it as `ContentDisposition: attachment; filename="..."` on upload (`app/storage.py`). No backend grant needed; drop the `sheets.ts:559-561` half of B-79 from this wave (log a backlog item if the download-filename fix doesn't fully satisfy it).
- T-9-5 AC1 ("the backend client retries" on 429/Retry-After) requires an edit to `invai-backend/src/integrations/imaging/client.ts`, which is outside `invai-imaging`. Added as a narrow grant above (single `call()` function, one retry branch) rather than a 6th card.

### Decision: PDF rasterizer path (T-9-1)
Checked the installed wheel directly: `pyvips[binary]==3.2.0` bundles libvips 8.18.6 with **no `pdfload`** (`hasattr(pyvips.Image, "pdfload")` → `False`, confirmed by running it). Checked alternatives:
- **pypdfium2**: pip-only wheel with a bundled prebuilt pdfium — installs and imports cleanly on macOS arm64 dev with no system packages, and PyPI publishes `manylinux_2_17_x86_64` wheels (verified downloadable) which are ABI-compatible with the imaging Dockerfile's `python:3.13-slim` base — **no Dockerfile change needed**.
- **poppler** (`pdf2image`/`python-poppler`): both need the `poppler-utils` system binary, absent from `python:3.13-slim`; would need an `apt-get` line in the Dockerfile plus a separate Homebrew install for macOS dev parity. More moving parts, worse cross-platform story, for the same outcome.
- **Decision: use pypdfium2.** Add `pypdfium2>=5` to `pyproject.toml`. New `app/pdf_input.py::rasterize_pdf(path, dpi) -> pyvips.Image` renders page 1 via `pdfium.PdfDocument`, feeds the bitmap into `pyvips.Image.new_from_buffer` so the rest of the pipeline (compose/QA/render) sees a normal vips image. Multi-page input art is rejected with a clear 422 (`len(doc) > 1`), since art uploads are single-page by contract.

### Decision: T-9-3 — cap, not split
**Cap `maxLengthIn` at 200in, for `format: "pdf"` only** (PNG keeps the current 240in ceiling — a PNG has no page-size/`/UserUnit` concept, so it isn't the bug B-80 describes).
- Splitting into ≤200in pages with alignment marks would double `app/pdf.py`'s surface (page layout, registration marks, re-assembly tests) to serve a case that's rare at the segment this wave targets — `product/scope.md` has pilots starting **mid**, with **large** shops (the ones most likely to run >200in jobs) gated behind `scale-test`.
- CADlink and comparable RIPs expect one continuous image per barcode/job-name lookup (`research/10-marketplace-engineering-rules.md` DTF section); a multi-page PDF pushes re-assembly work onto the press operator, which is a worse outcome for the self-serve/assisted segments than just capping.
- 200in × 72pt = 14,400pt is exactly the existing `MAX_PAGE_PT` constant — capping removes the `/UserUnit` branch in `app/pdf.py` entirely instead of special-casing it: smaller diff, one less thing to test.
- Enforcement point: `SheetSpec` save validation (contracts + backend), not just imaging — a shop should get the "pick PNG or shorten the sheet" error before a sheet is ever queued, not at compose time. `app/pdf.py` keeps a defensive `ImageError` as a second line of defense.

### Contract changes (exact)
`invai-contracts/src/schemas/vendors.ts` — `SheetSpec`:
```ts
export const SheetSpec = z.object({
  widthIn: Inches.max(60),
  maxLengthIn: Inches,
  format: z.enum(["png", "pdf"]),
  dpi: z.number().int().min(36).max(1200),
  pricePerInch: Cents.nonnegative(),
  spacingIn: z.number().nonnegative(),
  marginIn: z.number().nonnegative(),
  labelGapIn: z.number().nonnegative().default(0.125), // was hardcoded LABEL_GAP_IN=0.04 in compose.py
  colorProfile: z.string().nullable(),
  notes: z.string().nullable(),
}).refine(
  (s) => s.format !== "pdf" || s.maxLengthIn <= 200,
  { message: "PDF sheets are capped at 200in; use PNG for longer runs.", path: ["maxLengthIn"] },
);
```

`invai-contracts/src/schemas/personalization.ts` — `TemplateSlot` (font enum already existed as `TEMPLATE_FONTS` but wasn't wired up — that's the actual B-81 bug):
```ts
export const TemplateSlot = z.object({
  name: z.string().min(1).max(40),
  kind: z.enum(["text", "photo"]),               // was z.literal("text")
  xIn: z.number().nonnegative(),
  yIn: z.number().nonnegative(),
  wIn: Inches,
  hIn: Inches,
  fontFamily: z.enum(TEMPLATE_FONTS),             // was z.string() — wire up the existing enum
  fontSizePt: z.number().positive(),
  minFontSizePt: z.number().positive().nullable().default(null), // absolute shrink floor; null = 60% default
  maxLines: z.number().int().positive().nullable().default(null),
  strokeWidthPt: z.number().nonnegative().default(0),            // outline
  strokeColor: z.string().regex(/^#[0-9a-fA-F]{6}$/).nullable().default(null),
  fit: z.enum(["fit", "fill"]).default("fit"),    // photo slots only
  color: z.string().regex(/^#[0-9a-fA-F]{6}$/),
  align: z.enum(["left", "center", "right"]),
  maxChars: z.number().int().positive().nullable(),
  uppercase: z.boolean(),
  sourceQuestion: z.string().nullable(),
  required: z.boolean(),
  placeholder: z.string().nullable(),
});
```
Add a template-level check (contracts `.refine` on `PersonalizationTemplateInput`, mirrored by a Pydantic validator on `TemplateModel` in `app/main.py` — imaging is the actual authority, contracts just fail fast): every slot's `xIn+wIn <= widthIn` and `yIn+hIn <= heightIn`, and slot `name`s unique. Also bound `PersonalizationTemplateInput.widthIn/heightIn` at `.max(60)` and `dpi` at `.min(36).max(1200)`, mirroring T-9-5 AC2's imaging-side bounds. Add `"low_res_photo"` to `ARTWORK_FLAG_CODES`.

`app/main.py`'s `SlotModel.font_family` must be validated against `app/fonts.py`'s known families and return a 422 on an unknown name — the current silent fallback to Inter (`fonts.py:31-33`, `normalize_family`) is the literal bug; don't just add the enum upstream and leave the imaging-side fallback in place.

### Acceptance-criteria testability notes (see reviews for the full list)
- T-9-1 AC3 "visual checksum" is unspecified — since rendering is deterministic, tests should hash decoded raw pixels (not the compressed file) and compare against a fixed digest per fixture/DPI.
- T-9-2 AC1 "if they can't fit, compose fails loudly" needs a precise trigger: define the minimum label-strip height in inches below which a 0.5mm-module QR cannot be laid out at the sheet's DPI, and assert `ImageError` at exactly that boundary.
- T-9-4 AC1 "auto-shrink down to a minimum font size" is now two knobs (`minFontSizePt` absolute vs. the existing 60%-of-size default) — the card should state which wins when both apply (the larger of the two, so a slot never shrinks past whichever floor is more generous).
- T-9-5 AC2 needs two concrete gaps closed to be testable at all: `ComposePlacementModel` lists and `ComposeRequest.width_in`/`NestRequest.sheet_width_in` currently have no `max_length`/`le=60` bounds in `app/main.py` — add them before writing the "oversized input" test.
