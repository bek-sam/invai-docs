# T-9-4: Personalization upgrades (B-81)
Evidence: §A-INF B-6, B-7, B-8 (`main.py:111`, `fonts.py:31-33`, `render.py`).
## Acceptance criteria
1. **Multi-line text:** wraps within the slot box, with a max-lines setting, auto-shrink down to a minimum font size, and a flag when it overflows.
2. **Outline:** stroke width and color, for dark shirts.
3. **Photo slot:** upload a buyer photo (JPEG, PNG, HEIC, WebP), fit or fill into the slot, with a DPI check that flags low resolution.
4. **Fonts:** `fontFamily` becomes an enum in contracts (`TEMPLATE_FONTS`). An unknown font is rejected, not silently swapped for Inter. Characters missing from the chosen font are flagged, with the missing characters listed.
5. **Template geometry:** slots outside the template bounds, or with duplicate names, are rejected at save.
6. **Web:** the template editor shows the new slot options, in en/es.
7. **Tests** for each item.

## Plan review r1 — files, sequencing, contract diff, testability
Runs in the **3-way parallel batch** (see `wave.md` §Plan review r1), after T-9-1 lands.

**Owns:** `app/render.py`, `app/fonts.py` (plus the one-line `load(bg, target_dpi=...)` call for template backgrounds once T-9-1's `vips.py` change is in), and the `invai-web` template editor. **Narrow grants only:** `app/main.py`'s `SlotModel`/`TemplateModel` classes; `invai-contracts/src/schemas/personalization.ts`; `invai-backend/src/integrations/imaging/client.ts` (mirror the same `TemplateSlot`/`kind` fields so the backend's zod copy doesn't drift — it's currently a hand-kept duplicate per B-104).

**Contract diff (also in `wave.md`):** `TEMPLATE_FONTS` already exists in `invai-contracts/src/schemas/personalization.ts` but `TemplateSlot.fontFamily` is still `z.string()` — wire it to `z.enum(TEMPLATE_FONTS)` rather than adding a new enum. Add `kind: z.enum(["text","photo"])` (was `z.literal("text")`), `minFontSizePt`, `maxLines`, `strokeWidthPt`, `strokeColor`, `fit`. Add a template-level `.refine()` (mirrored by a Pydantic validator on `app/main.py`'s `TemplateModel`, which is the actual authority): every slot's `xIn+wIn <= widthIn`/`yIn+hIn <= heightIn`, names unique. Add `"low_res_photo"` to `ARTWORK_FLAG_CODES`.

**Fix the real bug, not just the contract:** `app/fonts.py:31-33`'s `normalize_family` silently falls back to Inter on an unknown name — that fallback is B-81 itself. `SlotModel.font_family` in `app/main.py` must 422 on a name not in `fonts.py`'s known families; adding the contracts enum alone doesn't fix this if the imaging-side fallback stays.

**AC1 testability:** "auto-shrink down to a minimum font size" is now two knobs — the new absolute `minFontSizePt` and the existing 60%-of-size (`MIN_SCALE`) default. State which wins when both apply (recommend: the *larger* of the two floors, so a slot never shrinks past whichever is more generous) before writing the shrink test.
