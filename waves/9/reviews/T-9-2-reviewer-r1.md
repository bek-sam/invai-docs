# Review of T-9-2 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: imaging-engineer on Sonnet
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-imaging show <commit> --stat` for `6b9c8f3 d670063 d4e3ddb 0e5a93e 19d53af c974ff4 3793c47 c872d19` | Every file touched is in the card's owned paths (`app/compose.py`, `app/storage.py`) or a granted narrow class/field (`app/main.py`'s `NestRequest`/`ComposeRequest` — `header_height_in` grant recorded in `wave.md`) or test files; `c872d19` is the separately-granted `app/labels.py` ruff-format fix |
| `git -C invai-contracts show ba59371 --stat` | Only `src/schemas/vendors.ts`, 2 lines (`labelGapIn`) — matches the architect's exact diff |
| `git -C invai-backend show <commit> --stat` for `00fb593 4a73828 8b728b1 5ba3c8f` | Only `db/schema/vendors.ts`, `integrations/imaging/client.ts`, `modules/production/sheets.ts`, `db/seed/builder.ts` — all granted ("sheet-spec pass-through", `filename_hint`, `LABEL_HEIGHT_IN`, `HEADER_HEIGHT_IN`) |
| `uv run ruff check . && uv run ruff format --check .` (invai-imaging) | All checks passed!, 31 files already formatted |
| `uv run pytest -q` (invai-imaging) | 102 passed, 0 failed |
| `pnpm typecheck && pnpm test` (invai-contracts) | tsc clean; 31/31 vitest passed |
| `pnpm typecheck` (invai-backend) | clean |
| `pnpm biome check` on the 4 touched backend files | Checked 4 files, no issues |
| `TEST_DATABASE_URL=.../invai_review_t92 pnpm vitest run production/{print-bins,jobs,production,matcher,pack}.test.ts` (fresh scratch DB, dropped after) | 38/38 passed |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-imaging origin/main` | Hits are all dimension/offset assertions updated to the new `label_height_in`=0.42/`header_height_in`=0.45 values (e.g. `1800,1200`→`1800,1350`, `p.y_in >= margin`→`>= margin+header`), strictly stronger, not weaker; one test (`test_long_sheet_pdf_uses_user_unit`) moved to `tests/test_pdf.py` under T-9-3's B-80 cap decision, unrelated to this card, still covered there |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend origin/main` | 0 assertions removed, 32 added; one `it(...)` addition is T-9-5's 429-retry test, unrelated |
| **Real run:** `uv run uvicorn app.main:app --port 8123` against real MinIO with `X-Imaging-Secret: invai-imaging-dev-secret` | `/sample-art` → design; `/nest` with 3 default-size items, default settings → `y_in=0.7` (= 0.25 margin + 0.45 header) for the first row, `length_in=11.37` |
| `/compose` at dpi 150/200/300, same placements, `filename_hint="REVIEW-SHEET 1001 1002"`, default `label_height_in`/`label_gap_in`/`header_height_in` | All 3 composes succeeded (200) |
| Downloaded each PNG from MinIO (boto3), `head_object` | `ContentDisposition: attachment; filename="REVIEW-SHEET 1001 1002.png"` on all 3 |
| `zxingcpp.read_barcodes()` on each downloaded sheet | 4/4 codes decoded at every DPI: the 3 transfer UUIDs verbatim + the header text, byte-identical to input |
| Visual inspection of the 300 DPI sheet | Header strip top-left (QR + "REVIEW-SHEET 1001 1002"), designs not overlapping the header, dashed cut guide visible under each design before its label strip, labels readable, REPRINT/rotation not clipped |
| `curl /compose` with `label_height_in=0.05` | 422 `"label strip too short for a scannable QR: 27 modules need >= 0.351in ... only 0.050in available"` — AC1 fails loudly with a precise, geometric message |
| `git show 6b9c8f3^:app/compose.py` vs current `qr_image`/`render_label` | `qr.add_data(data)` where `data` is the bare `transfer_id`, unchanged before and after this card — no wrapper/prefix added, so `invai-floor/src/lib/codes.ts`'s `transferIdOf` (bare-code fallback) still parses it identically |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Transfer QRs always >=300 DPI-equivalent, >=0.33mm/module (tech-lead-corrected floor), fail loudly if they can't fit | Yes | `qr_image`/`_qr_bitmap` build from `max(dpi, QR_MIN_DPI=300)` and resample down; `MIN_MODULE_MM=0.33`; `test_qr_module_floor_is_dpi_independent` and my own 422 trigger above confirm the exact boundary |
| 2. Sheet header barcode/QR with sheet id; file name carries sheet id + order numbers via `ContentDisposition` | Yes | `render_header`/`header_qr_image` draw a QR+text into a dedicated `header_height_in` (0.45in) band; `storage.upload(..., download_filename=filename_hint)` sets `ContentDisposition`; confirmed live (real MinIO header decode + `head_object` above). AC2's S3-key half was correctly descoped per `wave.md`'s plan-review note (opaque keys stay opaque) |
| 3. Configurable label gap, default 0.125in, thin cut guide | Yes | `SheetSpec.labelGapIn` default 0.125 (contracts + backend mirror); `render_cut_guide` draws a dashed line in the gap, visually confirmed; `label_gap_in` positions the label without eating its content height (`d670063`) |
| 4. Tests decode QRs at 150/200/300 DPI + header | Yes | `test_compose_qr_decodes_at_multiple_dpi`, `test_compose_header_decodes`, `test_default_settings_header_and_transfer_qrs_all_decode` (real `nesting.nest()` → `compose_sheet()`, default settings, fresh UUIDs) all pass; matches my own live proof exactly |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat` per commit, see evidence)
- [x] Nothing outside scope — `app/main.py` touches limited to `NestRequest`/`ComposeRequest` classes (verified with `git diff 87e01e0..c872d19 -- app/main.py | grep '^@@'`); backend touches limited to the granted sheet-spec pass-through / `filename_hint` / constant bumps
- [x] Tests exercise the behavior, and none were weakened (scan output reviewed above; all hits are stronger, updated, or moved to the owning card's test file)
- [x] Tenancy n/a (no tenant tables touched); idempotency n/a (pure render, same input -> same output key overwrite, unchanged); money n/a; en/es n/a (no user-facing UI text, label strings are order metadata); `ContentDisposition` value is sanitized (quotes/CR/LF stripped) before going in a header, no injection
- [x] Decisions recorded — tech lead's 0.33mm floor, 0.42in label default, 0.45in header strip are all in `wave.md` and cross-referenced correctly in commit messages and the report

## Optional notes (not blocking)
1. No dedicated backend unit test file exists yet for `sheets.ts`'s `composeSheet()`/`imaging.compose()` call shape (label_gap_in/filename_hint/header_height_in wiring) — covered today by `pnpm typecheck` (excess-property check on the call site) and by my own live end-to-end proof, but a `sheets.test.ts` asserting the exact object passed to `imaging.compose()` would catch a future silent drop of one of these fields without needing a live imaging run.
2. `render_header`/`render_label` both silently truncate long text with an ellipsis when the header/label strip is narrow — fine as designed (never fails compose), but worth a card note if very long `filename_hint`s (150 chars, shop name + many order numbers) turn out to be truncated to the point of being useless in practice on a narrow film.
