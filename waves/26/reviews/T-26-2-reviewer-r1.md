# Review of T-26-2 (round 1)

- Reviewer: reviewer on fable
- Author: imaging-engineer on opus (invai-imaging `f282280`, not pushed)
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `uv run ruff check . && uv run ruff format --check . && uv run pytest -q` | exit 0, 159 passed in 6.05 s |
| `scan-test-weakening.sh invai-imaging origin/main` | no hits (removed=0, added=74); no skip/only/mock in tests/test_photos.py |
| `git show --stat f282280`; `git status --short` | 9 files, all `invai-imaging/**` (no Dockerfile); tree clean |
| uvicorn :8151 (PID 73033, stopped; port free after) | `/health` ok, vips 8.18.6 |
| `POST /photo/render` tee/front_flat/amazon_main, #000000, underbase, xmp | 200; print_box 645×737 px = 10.5×12 in at 61.4 ppi; `background_pure_white: true`, fill 0.90, failures `["illustration_not_photo"]`, passes false |
| `POST /photo/render` tee/folded/etsy #FFFFFF; tee/front_flat/etsy; hoodie/on_model_white/etsy #1B3A6B | 200 ×3; 2700×2025; folded box 1151×1315 (109.6 ppi), flat 653×746 (62.2 ppi); hoodie scale 0.75 + `design_larger_than_print_area` (9 in area) |
| Refused: design_key in another company → 400; zip item in another company → 400 (`items[1].key`); no secret → 401; non-UUID prefix → 400; `out_key` `.exe` → 422 | all as the card requires |
| `POST /photo/palette`, `/photo/zip` (name `../../etc/passwd.jpg`), `GET /photo/templates` | palette 200 deterministic; zip entries `amazon/01 tee.jpg`, `etc/passwd.jpg` (traversal stripped); 16 templates, tee front 12×16 / back 14×16 |
| Downloaded 4 outputs from MinIO and looked at them; `xpacket`+`contains-synthetic-performer` in amazon.jpg, absent in etsy-folded.jpg; flat px (528,1823) = [0,0,0] on the black render | ok |
| Strict white probe on amazon.jpg: pixels not 255 with product mask == 0 | 9665 px, min channel 241, all inside the 8×8-block halo the check excludes; block-grown check true |
| `PYTHONPATH=. /usr/bin/time -l uv run python bench/photo_bench.py /tmp/t262r/sheet.jpg` | cold 0.283 s avg (max 0.484), warm 0.119 s, zip 48 = 0.034 s / 8.8 MB, peak RSS 602 MB; contact sheet looked at |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Templates | yes | 16 drawn by bezier code in `app/garments.py` (no assets); print areas tee 12×16 (top 3 in under collar), hoodie 12×9 above pocket, tank 10×13; shadow/highlight/height maps; folds visibly darken and bend on the sheet |
| 2 Real size/color | yes | px = round(in × ppi) in both views I rendered; never upscaled (`_place` scale ≤ 1); 14×18 → 0.75 + failure code (test + hoodie render); flat pixel == hex (16 param tests + my probe); back skip documented README:123 |
| 3 Underbase | yes | tests dark/light; `underbase_applied` true on #000000 and #1B3A6B, false on #FFFFFF |
| 4 Presets/checks | yes | 6 preset tests (size, JPEG sRGB, icc, white, fill, longest); `illustration_not_photo` only on amazon_main; wording to compliance-officer |
| 5 XMP | yes | test jpg+png; my read-back of amazon.jpg; none on empty list |
| 6 Palette | yes | tests; live call deterministic |
| 7 Zip | yes | stdlib zipfile; traversal name sanitised live; cross-company 400 live |
| 8 Safety/budget | yes (RSS gap disclosed) | 401/400 live; `_design` runs `load()` (allowlist + declared-type + pixel cap) before `thumbnail`; palette through `load()`; HEAVY_PATHS test; time met, RSS 602 MB over the 16-set reported honestly |
| 9 Contact sheet | yes | `/tmp/t262/contact-sheet.jpg` (author) and `/tmp/t262r/sheet.jpg` (mine) looked at; illustration note in report |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`git diff --stat`)
- [x] Nothing outside scope (`/mockup` untouched; no scene routes)
- [x] Tests exercise the behavior, and none were weakened
- [x] Tenancy: company prefix (UUID first segment) checked on every key incl. zip items vs `out_key`; no PII in logs; Pydantic on every input; n/a money/en-es
- [x] Decisions recorded in the report (anchor, fill_ratio, block rule, 400); none cross-cutting beyond the ADR

## Optional notes (not blocking)
- Folded views (tech lead's question): not a scale bug. The folded template is a smaller object (14 × 16.6 in vs 29 × 29 in flat) that `FILL=0.90` zooms to the frame, so ppi is 1.76× the flat view and a 10.5 in design is 1151 px vs 653 px; the inch math is consistent. The cut at the bottom is the fold-under at 16.6 in below the shoulder: a 12×16 print starting 3 in under the collar reaches 22.6 in, so its lower 6 in sits on the folded-back part. Physically right, but as a listing photo it hides a chunk of any max-size front print; suggest the product-designer decide whether the fold should sit below the print area (~23 in) for the folded view (`garments.py:483-500`).
- `background_pure_white` excludes a ≤7 px halo (8×8 blocks touching the product); I measured 9,665 pixels down to 241 there on amazon_main. Documented in README:137; compliance-officer should confirm Amazon's tooling tolerates this (any JPEG edge does it).
- `fill_ratio` is a template constant (0.90 flat, 0.95 on-model) from the mask bbox, not measured on the encoded file; fine while templates are drawn, note for the scene composite in wave 27.
- The report's bench command fails as written (`No module named 'app'`); it needs `PYTHONPATH=.` (README:183 too).
- `/photo/zip` downloads up to 500 objects with no size cap on each; same as existing routes, backend caps uploads.
