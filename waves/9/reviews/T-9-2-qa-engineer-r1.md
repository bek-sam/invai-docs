# Review of T-9-2 (round 1)

- Reviewer: qa-engineer on Sonnet 5
- Author: imaging-engineer on Sonnet
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `uv run pytest -q` (invai-imaging) | 102 passed, 0 failed |
| `uv run ruff check . && uv run ruff format --check .` | All checks passed! |
| Started `uv run uvicorn app.main:app --port 8123` against real MinIO (`X-Imaging-Secret: invai-imaging-dev-secret` from `.env.example`) | Healthy |
| `/sample-art` (dev endpoint) to create a real design PNG | `{"key":"review/design1.png"}` |
| `/nest` — 3 items (10x10, 8x6, 5x5), **all-default** `spacing_in`/`margin_in`/`label_height_in`/`header_height_in` | 1 sheet, `length_in=11.37`, first row `y_in=0.7` (0.25 margin + 0.45 header, matches `wave.md`'s decision) |
| `/compose` at dpi **150, 200, 300** — same placements, all-default `label_height_in`(0.42)/`label_gap_in`(0.125)/`header_height_in`(0.45), `filename_hint="REVIEW-SHEET 1001 1002"` | All 3 return 200 with pixel sizes exactly `round(width_in*dpi) x round(length_in*dpi)` (3300x1705, 4400x2274, 6600x3411) |
| Downloaded each sheet PNG from MinIO via boto3, ran `zxingcpp.read_barcodes()` | **150/200/300 DPI: all 3 transfer QRs + the header QR decode, 4/4 each time**, text byte-identical to the input UUIDs/`filename_hint` |
| `head_object` on each uploaded key | `ContentDisposition: attachment; filename="REVIEW-SHEET 1001 1002.png"` present at every DPI |
| Opened the 300 DPI sheet and looked at it | Header band top-left, clear of every design; dashed cut guide between each design and its label; labels legible, none clipped or overlapping the header |
| `curl /compose` with `label_height_in=0.05` (below the 0.33mm-floor boundary for a real UUID) | 422, `"label strip too short for a scannable QR: 27 modules need >= 0.351in ... only 0.050in available at 300 DPI"` — fails loudly, not silently degraded |
| Floor-scan parity check: `git show 6b9c8f3^:app/compose.py` (pre-card) vs current `qr_image` | Both call `qr.add_data(data)` with `data` = the bare `transfer_id` string, no prefix/wrapper added by this card |
| Read `invai-floor/src/lib/codes.ts` | `parseCode`/`transferIdOf` fall through to `{kind:"unknown", value:raw, raw}` for a bare code (no `T:`/`B:`/`BIN:` prefix, not a 12-14 digit UPC), and `transferIdOf` returns `p.raw` in that branch — i.e. the exact scanned string. Since the QR payload is still the bare UUID (unchanged), the floor's scan parsing is unaffected by this card |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-imaging origin/main` | All hits are dimension assertions updated to the new label/header defaults (stronger, not weaker) or a test relocated to `test_pdf.py` under T-9-3's unrelated B-80 decision |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Transfer QRs >=300 DPI-equivalent raster, >=0.33mm/module, fail loudly if they don't fit | Yes | Live 422 above at the exact geometric boundary; `test_qr_module_floor_is_dpi_independent`/`test_compose_fails_loudly_when_label_strip_too_short` pass |
| 2. Header barcode/QR with sheet id; file name (via `ContentDisposition`) carries sheet id + order numbers | Yes | Live header decode at all 3 DPIs; live `ContentDisposition` confirmed on the S3 object; opaque S3 key correctly left untouched per `wave.md`'s scope note |
| 3. Configurable label gap, default 0.125in, thin cut guide | Yes | Visually confirmed dashed cut guide on the composed sheet; `SheetSpec.labelGapIn` default 0.125 in contracts and backend mirror |
| 4. Decoder tests at 150/200/300 DPI + header decode | Yes | `test_compose_qr_decodes_at_multiple_dpi`, `test_compose_header_decodes`, `test_default_settings_header_and_transfer_qrs_all_decode` all green; independently reproduced live with a decoder against a real composed sheet, not just the test fixtures |

## Blocking findings
None.

## Checks
- [x] Only owned/granted paths changed (spot-checked per-commit `--stat` against the card's `Owns:`/grant lines)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened (scan run, hits reviewed — all are strengthened or relocated, not loosened)
- [x] Floor-correctness (this card's risk flag): the transfer QR's encoded payload (`transfer_id`, no prefix) is byte-for-byte unchanged from before this card, and decodes correctly at every DPI the floor might encounter downstream; `invai-floor`'s scan parser (`parseCode`/`transferIdOf`) requires no change and was not touched
- [x] Money/tenancy/idempotency n/a for this card's surface (pure rendering, no tenant data, no side effects beyond overwriting the same output keys)
- [x] Decisions recorded — the 0.33mm floor correction, 0.42in label default and 0.45in header band are each dated and attributed in `wave.md` and mirrored correctly in the commits I reviewed

## Optional notes (not blocking)
1. The header/label text-truncation behavior (ellipsis when the strip is too narrow for the full string) was not separately exercised with a very long `filename_hint` close to the 150-char cap; low risk since it only affects the printed courtesy text, not the QR payload itself (the QR always encodes the full string or is dropped, never truncated).
2. Backend's `sheets.ts` compose call has no dedicated unit test asserting the exact `label_gap_in`/`filename_hint`/`header_height_in` fields sent to `imaging.compose()` — today's safety net is `pnpm typecheck`'s excess-property check plus this review's live end-to-end run. Not blocking; would be a cheap addition for the next backend card that touches this call site.
