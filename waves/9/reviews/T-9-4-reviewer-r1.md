# Review of T-9-4 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: imaging-engineer + web-engineer on Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-contracts show --stat ad3d9cc` / `invai-imaging a5fd3b5` / `invai-backend f1f1f40` / `invai-web 80fc945` | Every touched path matches the card's owned/granted paths exactly |
| `invai-imaging`: `uv run ruff check .` | clean |
| `invai-imaging`: `uv run pytest -q` | 71 passed |
| `invai-contracts`: `pnpm typecheck && pnpm test` | clean; 31 passed |
| `invai-backend`: `pnpm typecheck` | clean (repo has unrelated in-flight changes from other cards; not this card's diff) |
| `invai-backend` on scratch DB `review_t94`: `pnpm vitest run src/modules/personalization/render-job.test.ts src/modules/orders/import.test.ts` | 15 passed |
| `invai-backend` on scratch DB: `pnpm vitest run src/modules/personalization/security.test.ts` | 1 passed; DB dropped after |
| `invai-web`: `pnpm typecheck && pnpm lint` | clean |
| `invai-web`: `pnpm vitest run src/features/personalization/fit.test.ts` | 6 passed |
| `.claude/skills/independent-review/scan-test-weakening.sh <repo> origin/main` (all 4 repos) | see below |
| Ran imaging locally (`uv run uvicorn app.main:app --port 8091`), `curl POST /render/personalization` with a template shaped like the seed's `textSlot` (kind text, all new fields at their defaults) | `200`, `{"flags":[]}`, correct pixel size — golden-path render still works |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Multi-line wrap, max-lines, shrink, overflow flag | Yes | `app/render.py::fit_lines`/`_wrap`; `tests/test_render.py` (`test_fit_lines_wraps_across_multiple_lines_when_it_fits`, `test_fit_lines_flags_overflow_past_max_lines`, `test_min_font_size_pt_wins_when_more_generous_than_min_scale`); mirrored in web `fit.ts`/`fit.test.ts` |
| 2. Outline | Yes | `render_slot()` draws `stroke_width`/`stroke_fill`; `test_outline_stroke_widens_the_glyph_ink`; web preview draws SVG `stroke`/`paintOrder` |
| 3. Photo fit/fill + DPI flag | Yes | `render_photo_slot()`; `test_photo_slot_fit_letterboxes_and_fill_covers`, `test_low_res_photo_is_flagged`; API round-trip `test_personalization_photo_slot_end_to_end` |
| 4. Unknown font rejected, missing glyphs listed | Yes | `fonts.normalize_family` raises; `SlotModel.font_family` validator 422s (`test_personalization_rejects_unknown_font`); `fonts.missing_chars` + `check_text` flag (`test_missing_glyphs_flag_lists_unsupported_characters`) |
| 5. Geometry / duplicate-name validation | Yes | `main.py TemplateModel._check_geometry` (422s, `test_personalization_rejects_duplicate_slot_names`/`..._outside_template_bounds`); backend `validateSlots()` is the real authority on create/update, contracts `.refine()` fast-fails on create |
| 6. Web editor shows new options in en/es | Yes | `personalization.$templateId.tsx` diff; every new key present in both `en.ts` and `es.ts` at matching positions |
| 7. Tests for each item | Yes | see above, plus `tests/test_fonts.py` (new) |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git show --stat` per commit matches card's owns/grants)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened. Scan hits reviewed: imaging's removed-assertion hits are from T-9-2/T-9-3 commits sharing the repo (`test_compose.py`, `test_pdf.py`, etc.), not T-9-4's files — `a5fd3b5`'s own diff to `tests/test_api.py`/`test_render.py`/`test_fonts.py` is additions only. Web's two "removed" lines in `fit.test.ts` are a like-for-like rename (`.text` → `.lines`, still asserted via `.lines.join(" ")`/`tooLong`) plus a split into two more specific tests — equal or stronger coverage, not a weakening. Backend's untracked `src/api/orpc.test.ts` is unrelated in-flight work from another card.
- [x] Tenancy / idempotency n/a to this diff (no new tables, no side effects); money n/a; en/es text present for every new string
- [x] Decisions recorded: wave.md's "larger of the two floors" testability decision is implemented identically in imaging (`fit_lines`) and web (`fitSlotText`)

## Optional notes (not blocking)
- **Buyer-photo upload is out of scope for this card.** AC3 says "upload a buyer photo" but this card owns the template editor (configuring slot geometry/fit) and the render path (`render_photo_slot`, `SlotModel.kind == "photo"` download-by-key), both of which are fully implemented and tested. No card in wave 9 owns a buyer- or staff-facing upload endpoint/UI to produce the storage key in the first place, and none existed before this card either — it isn't a regression or a dropped requirement, it's a new surface (channel intake / order-item artwork) that belongs to a future card. The report flags this explicitly rather than silently dropping it, which is the right call; recommend a backlog item if not already logged.
- `_wrap()`'s word-wrap in both imaging and web splits on whitespace only, so a value with no spaces (e.g. some non-Latin scripts) won't wrap mid-word — acceptable for v1 given the en/es scope, but worth a backlog note if buyer names in other scripts become common.
