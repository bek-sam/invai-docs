# T-9-4: Personalization upgrades (B-81)

## What changed

**invai-contracts** (commit `ad3d9cc`)
- `src/schemas/personalization.ts`: `TemplateSlot.kind` becomes `z.enum(["text", "photo"])`
  (was `z.literal("text")`); `fontFamily` is wired to `z.enum(TEMPLATE_FONTS)` (was `z.string()`
  — `TEMPLATE_FONTS` already existed but wasn't enforced, the actual B-81 bug). Added
  `minFontSizePt` (absolute shrink floor, null = 60% default), `maxLines`, `strokeWidthPt`/
  `strokeColor` (outline), `fit` ("fit"|"fill", photo slots only).
- `PersonalizationTemplateInput` gains two `.refine()`s: unique slot names, and every slot's
  `xIn+wIn`/`yIn+hIn` inside the template's `widthIn`/`heightIn`. Split out
  `PersonalizationTemplateInputShape` (the same object, unrefined) because zod v4 refuses
  `.partial()` on a schema with `.refine()`s — the `update` route in
  `src/contract/personalization.ts` now calls `.partial()` on the shape instead. The real
  authority stays the backend's `validateSlots()` (already merges partial patches before
  checking), so this refine is a fast-fail on `create`, not the only check.
- `widthIn`/`heightIn` capped at 60in, `dpi` bounded 36-1200 on the input schema, mirroring
  imaging's own bounds. `ARTWORK_FLAG_CODES` gains `missing_glyphs` and `low_res_photo`.

**invai-imaging** (commit `a5fd3b5`)
- `app/fonts.py`: **fixed the actual bug** — `normalize_family()` now raises `ValueError` on an
  unknown family instead of silently returning Inter's key. Added `known_family()` for API-layer
  validation and `missing_chars(family, text)`, which flags characters the bundled font's cmap
  doesn't cover. Coverage is hardcoded per-font codepoint ranges (generated once offline with
  `fontTools` against each `.ttf`, via `uv run --with fonttools ...` — not added as a project
  dependency) rather than checked at runtime; all four bundled fonts fully cover ordinary Latin
  names, the gaps are all in rarely-used Latin Extended-B letters.
- `app/render.py`: rewritten for multi-line + outline + photo.
  - **AC1.** `fit_lines()` wraps text into at most `slot.max_lines` lines (greedy word-wrap) and
    picks the largest scale that fits the box; the floor is `max(MIN_SCALE, min_font_size_pt /
    font_size_pt)` — the *larger* (more generous) of the two, per the wave's testability
    decision. Past the floor, lines are clipped to `max_lines` and flagged `overflow` (same
    semantics as before, now multi-line-aware).
  - **AC2.** `stroke_width_pt`/`stroke_color` draw a Pillow stroke (`ImageDraw.text(...,
    stroke_width=, stroke_fill=)`) around each line.
  - **AC3.** `render_photo_slot()` fits (letterboxed, centered) or fills (scaled to cover,
    center-cropped) a downloaded photo into its box, using `pyvips` throughout (no Pillow
    decoding of untrusted photo bytes). Flags `low_res_photo` via `app.qa.effective_dpi()`
    against the slot's physical size when it would print under the existing 150 DPI floor
    (`qa.DPI_ERROR`). HEIC/WebP/JPEG/PNG are handled by the existing `app.vips.load()` (libvips
    auto-detects format; `heifload`/`webpload` are present in the `pyvips[binary]` wheel —
    checked live).
  - **AC4.** `check_text()` now also calls `fonts.missing_chars()` and flags `missing_glyphs`
    with the offending characters listed.
- `app/main.py` (narrow grant: `SlotModel`/`TemplateModel`):
  - `SlotModel.kind` adds `"photo"`; new fields mirror the contract; a `field_validator` on
    `font_family` 422s on a name `fonts.known_family()` doesn't recognize — **this is the
    concrete fix for B-81**, not just the contracts enum (an unknown name never reaches
    `render.py`'s old silent-fallback path at all now).
  - `TemplateModel` gets a `model_validator(mode="after")` rejecting duplicate slot names and
    slots that extend outside `width_in`/`height_in` (AC5).
  - The `/render/personalization` endpoint downloads a photo slot's value (a storage key, same
    pattern as `background_key`) before calling `render.render_personalization()`.
- Tests: `tests/test_fonts.py` (new — `known_family`, `normalize_family` raising,
  `missing_chars`), `tests/test_render.py` (wrap/max-lines/min-font-size-floor, stroke widens
  ink bbox, photo fit-vs-fill, `low_res_photo`, `missing_glyphs`), `tests/test_api.py`
  (unknown-font 422, duplicate-name 422, outside-bounds 422, a full photo-slot round trip via
  the API with a real uploaded JPEG).

**invai-backend** (commit `f1f1f40`, granted: personalization pass-through)
- `src/db/schema/personalization.ts`: `TemplateSlot` type mirrors the contract diff
  (`kind`/`fontFamily` narrowed to the same literal unions, new fields added). No migration —
  `slots` is a jsonb column (`jsonArray<TemplateSlot>()`), this is a TS-only type change.
- `src/modules/personalization/service.ts`: `renderTemplatePayload()` passes the new fields
  through to imaging's snake_case request; `localFlags()` skips the text-only date/year
  heuristics for photo slots (their value is a storage key, not buyer text — checking it against
  "looks like a date" would be meaningless and occasionally wrong).
- `src/integrations/imaging/client.ts`: `TemplateSlot`/`RenderResult` zod mirrors gain the same
  fields and the two new flag codes (per the card's explicit grant to keep this hand-kept
  duplicate from drifting, B-104).
- `src/db/seed/data.ts`, `src/modules/orders/import.test.ts`, `src/modules/personalization/
  render-job.test.ts`: the now-required slot fields added to existing literal/factory
  `TemplateSlot` objects (mechanical fallout of the contract diff, not owned by this card but
  needed to keep the repo typechecking — `import.test.ts` had unrelated concurrent T-8-6 work in
  it, staged with `git add -p` to include only this one hunk).

**invai-web** (commit `80fc945`, granted: template editor)
- `personalization.$templateId.tsx`: slot rows gain a Type (Text/Photo) select; photo slots show
  only geometry + a Fit/Fill select (no font/color/align/stroke fields, no Sample text input —
  there's no buyer-photo upload widget in the editor in this pass, see gap below). Text slots
  gain Min size (pt), Max lines, Outline width (pt) and Outline color inputs. All new UI strings
  added by hand to `src/i18n/en.ts` and `es.ts` (not run through `pnpm i18n`).
- `LivePreview` renders text as multiple `<tspan>`-equivalent `<text>` lines from `fit.lines`,
  draws the outline via SVG `stroke`/`paintOrder="stroke"`, and renders a placeholder box +
  label for photo slots (no real photo to show without an upload flow).
- `features/personalization/fit.ts`: `fitSlotText()` reworked to wrap text (character-count
  heuristic, same `GLYPH_RATIO` approach as before) up to `maxLines` and shrink to
  `minFontSizePt`'s floor when it's more generous than 60%, mirroring imaging's rule. Return
  shape changed from a single `text` to `lines: string[]`; `fit.test.ts` updated for the new
  shape and the new wrap/floor behavior (one existing case, "Maximiliano Fernández" in an
  unbounded-lines slot, now correctly wraps instead of overflowing — the old single-line-only
  assumption no longer holds, which is the intended AC1 change).

## Verification
- **invai-imaging**: `uv run ruff check . && uv run ruff format --check .` clean on touched
  files (one pre-existing, unrelated formatting issue in `app/labels.py`). `uv run pytest`:
  71/71 passed (full suite, including T-9-2's concurrent label-height-default commits landed
  during this session). Ran the service for real (`uvicorn` + `curl`) against local MinIO:
  rendered a two-line wrapped greeting and a stroked name, downloaded and looked at both PNGs —
  wrap, centering and the outline all render correctly (screenshots reviewed, not attached here).
- **invai-contracts**: `pnpm typecheck` and `pnpm test` clean (31/31, the pre-existing
  `.partial()`-on-refine failure this diff caused is fixed by the `Shape` split above).
- **invai-backend**: `pnpm typecheck` clean repo-wide; `pnpm lint` (biome) clean repo-wide.
  Personalization + orders + seed tests (`render-job`, `security`, `import`,
  `db/seed`) on a scratch DB (`TEST_DATABASE_URL`/`TEST_MIGRATION_DATABASE_URL=invai_test_t94`,
  dropped after): 48/48 passed.
- **invai-web**: `pnpm typecheck`, `pnpm lint` (biome), `pnpm build` all clean; `vitest run`:
  78/78 passed. Exercised the editor for real in a browser: logged in as
  `owner@desertbloom.test` against a locally-run api (`:3000`) + web (`:5173`, matching
  `WEB_ORIGIN` for CORS) dev server, opened a new template, switched a slot to Photo (form
  collapses to Fit/Fill + geometry, preview shows a placeholder box), switched back to Text,
  typed a long multi-word value (wrapped to two lines in the live preview, flagged `overflow`
  once it didn't fit even wrapped), and set a 4pt red outline (rendered correctly around the
  text in the SVG preview).

## Scope note: buyer photo upload
AC3 ("upload a buyer photo") is implemented end-to-end on the *render* path: a photo slot's
`values[name]` is a storage key, downloaded and composited (fit/fill, DPI-checked) exactly like
`background_key` already was. What this pass does **not** add is a buyer-facing or
staff-facing *upload* UI/endpoint to produce that storage key in the first place — that's a
different surface (channel intake / order-item artwork editing) than the template editor this
card owns, and no such endpoint existed before this card either. The template editor lets a shop
configure a photo slot (position, size, fit/fill) and the imaging service will render it
correctly once a key is supplied; wiring an actual upload control is flagged as a follow-up, not
silently dropped.

## Other notes
- `PersonalizationTemplate` (the read schema) inherits the new `TemplateSlot` shape
  automatically; no separate change needed there.
- Did not touch `invai-web/scripts/gen-i18n.py`'s generated defaults beyond what's needed — all
  new `pers.*` keys were added by hand to both `en.ts` and `es.ts`, alphabetically ordered to
  match the existing convention.
