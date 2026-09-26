# T-9-2: Sheet barcode, scannable QRs, label gap (B-79)

## Update 2 (2026-09-26): label_height_in default raised to 0.42in everywhere
Tech lead: raise `label_height_in`'s default to **0.42in** everywhere (imaging
`NestRequest`/`ComposeRequest`/`nesting.nest()`, backend `LABEL_HEIGHT_IN`, and anywhere else
0.35 lived), keep the 0.33mm floor, and prove a real compose decodes every transfer QR and the
header at 150/200/300 DPI with default settings.

**Landed:**
- imaging (`d4e3ddb`, `0e5a93e`, `19d53af`): `NestRequest`/`ComposeRequest.label_height_in` and
  `nesting.nest()`'s own default, all 0.35 -> 0.42; README's three mentions updated to match.
- imaging tests (`c974ff4`): `test_nesting.py`'s `LABEL` fixture constant matches; the AC1
  default-height test (previously `..._still_short_for_a_real_uuid`, documenting the gap) now
  flips to `test_default_label_height_decodes_a_real_uuid` and asserts success — 0.42in gives
  0.403in-need a real UUID a 0.017in margin at the 0.33mm floor.
- backend (`8b728b1`): `LABEL_HEIGHT_IN = 0.42`; `db/seed/builder.ts`'s own hardcoded `0.35` (a
  second, undeclared copy of the same constant in its greedy row-layout simulation) now imports
  `LABEL_HEIGHT_IN` instead of duplicating the number.
- `grep`ped both repos for every other `0.35`/label-height reference (`.claude/skills/
  imaging-change-with-budget/SKILL.md:25` also names 0.35 in prose, but that's outside any repo
  I commit to — not touched, flagging for whoever owns skill docs).

**Proved for real** (not just pytest): started `uvicorn app.main:app --port 8000` against real
MinIO, uploaded a design, called the live `/nest` then `/compose` with **default settings** (no
`label_height_in`/`label_gap_in` override) for 3 items each with a **fresh random UUID**
`transfer_id`, at `dpi` 150, 200 and 300, with a `filename_hint`. Downloaded each resulting PNG
from MinIO and decoded with `zxingcpp`:
- **All 3 transfer QRs decoded correctly at all three DPIs** (150/200/300) — AC1 confirmed at
  the new default, for real, not a cherry-picked fixture.
- **The header QR did not decode at any DPI.** Root cause, independent of `label_height_in`: the
  header's available height is the sheet's actual top *margin* (`margin_in`, default 0.25in in
  both `NestRequest` and `SheetSpec`/`DEFAULT_SHEET_SPEC`) — compose sizes the header to
  whatever clearance already exists above the first placement, specifically to avoid bleeding
  into a design (see the original report's design rationale). Even the smallest possible QR
  (version 1, `border=1`, `n=23`) needs `23 * 0.33mm = 0.299in` — already more than the 0.25in
  margin, for *any* non-trivial string, including a bare 7-char sheet id alone. This is a
  **third constant** (not `label_height_in`, not the module floor) blocking AC2's header at
  defaults; already flagged as a known gap in this report's original "Other gaps" section, now
  confirmed empirically. Not fixed here: `margin_in` is a whole-sheet edge margin (affects film
  cost/waste on all four sides, not just labels) and wasn't in this round's grant — flagging for
  a tech-lead decision rather than bumping it unilaterally. Smallest fix: `margin_in` default
  >= ~0.30in would fit a short sheet id; the fuller `filename_hint` (sheet name + order numbers)
  would need more.

**Re-ran the production tests** (fresh scratch DB, dropped after): `pnpm vitest run
production/{print-bins,jobs,production,matcher,pack}.test.ts` — 38/38 passed with the 0.42in
default.

**Seed gang-sheet efficiency: 69.1% avg (61.0-80.0% range, 25 sheets)** — below the 86-91%
documented in `team/lessons.md`. **Isolated the cause with an A/B control run**: reset+migrated+
seeded a second scratch DB with `LABEL_HEIGHT_IN` temporarily reverted to 0.35 (not committed,
restored immediately after) — result was 69.6% avg (61.0-81.0%), statistically the same. **The
0.42in change is not the cause.** `git log -- src/db/seed/builder.ts` shows only this card's
commit and the original T-5-3 "reusable seed builder" commit ever touched this file's greedy
row-packing/utilization math — so this seed has produced ~69% since T-5-3, regardless of
`label_height_in`, at either 0.35 or 0.42 (a +0.07in row overhead is negligible against this
seed's actual item sizes, which sampled at 3-14in tall, averaging ~11in -- not the small
logo-sized items the 0.35->0.42 change was reasoned about). The 86-91% figure in
`team/lessons.md` predates or measures something different than this exact builder path; T-9-2
didn't cause the gap and isn't the card to chase it down further (seed realism isn't owned
here) — flagging for whoever owns seed data / that lesson entry.

## Update (2026-09-26): tech lead's 0.33mm correction
Tech lead: the 0.5mm floor was a spec error; changed to **0.33mm** (13 mil, a common handheld
2D scanner minimum) so the 0.35in `label_height_in` default would work, and granted
`invai-backend/src/modules/production/sheets.ts` sending `filename_hint`.

**Landed** (commit `d670063`, imaging): `MIN_MODULE_MM = 0.33`. Also stopped `label_gap_in` from
shrinking the label's *content* height — it now only positions the label (and cut guide) below
the design, so AC1's floor and AC3's gap no longer compete for the same space. Tried dropping the
QR's quiet zone (`border=0`) to close the remaining gap; verified live (inside a real composed
sheet, not just the isolated bitmap) that it stops decoding — the QR's own corners then touch the
sheet's black background with no white margin left to separate the finder patterns, so zxingcpp
loses it. Reverted; kept `border=1`.

**Confirmed by decoding real composed sheets at 150/200/300 DPI, honestly: still short at
defaults.** A real (random) UUID transfer_id needs 31 modules with the quiet zone kept, i.e.
`31 * 0.33mm = 0.403in` of label content — geometry, independent of DPI. The default
`label_height_in` (0.35in, shared by imaging `NestRequest`/`ComposeRequest` and backend
`LABEL_HEIGHT_IN`, none owned/granted here) is **0.053in (1.35mm) short**. New parametrized test
`test_default_label_height_still_short_for_a_real_uuid` (150/200/300 DPI) pins this down exactly
and will start failing (a good thing — flip the assertion) once it's closed. All fixtures using a
taller `label_height_in` (e.g. this card's own tests, 0.8in) already pass at all three DPIs.

**Smallest closing move, for the tech lead:** bump `label_height_in`'s default from 0.35in to
somewhere >= 0.41in (0.45in for margin) in both imaging (`NestRequest`/`ComposeRequest`) and
backend (`sheets.ts`'s `LABEL_HEIGHT_IN`) — coordinated, neither owned/granted to T-9-2. A lower
floor won't reach it without dropping the quiet zone (unsafe, see above); encoding the UUID more
compactly (e.g. uppercasing so QR alphanumeric mode applies, `n` drops to 25 and fits, 0.325in)
would work but changes what the QR decodes to (no longer byte-identical to `transfer_id`) —
flagging, not doing, since floor-scanning's match logic (a different repo/card) may depend on
exact case.

**Landed** (commit `4a73828`, backend): `sheets.ts`'s `composeSheet()` now sends
`filename_hint: [sheet.name, ...uniqueOrderNos].join(" ")` (truncated to 150 chars) to
`imaging.compose()`; `client.ts`'s `compose()` input type gained the field. `pnpm typecheck`
clean; `TEST_DATABASE_URL`/`TEST_MIGRATION_DATABASE_URL=invai_test_t92` (dropped after) —
`pnpm vitest run` on `production/{print-bins,jobs,production,matcher,pack}.test.ts`: 38/38 passed.

## What changed

**invai-imaging** (commit `6b9c8f3`, on top of T-9-1 `bbb85a3` and T-9-3 `10c1aa2`)
- `app/compose.py`:
  - **AC1.** `qr_image()` now raises `ImageError` ("fails loudly") whenever the label strip's
    available square, at the sheet's own DPI, can't hold every module of the transfer QR at
    `MIN_MODULE_MM=0.5`. The check is pure geometry (`n modules x 0.5mm`, `n` from the actual
    `qrcode` matrix) — independent of DPI. When it passes, the QR is drawn from a master raster
    of `max(dpi, QR_MIN_DPI=300)` and resampled down to the sheet's own DPI, so a low-DPI sheet
    never gets a blockier code than a 300+ DPI one would. `qr_min_side_in(data)` exposes the
    boundary as a pure function for tests. The header QR (`header_qr_image`) uses the same
    construction but returns `None` (blank header) instead of raising — a missing header never
    fails compose, unlike a transfer label.
  - **AC2.** Optional `filename_hint` param: when given, a header strip is drawn at the top of
    the sheet with a second QR + text encoding it, sized to whatever clearance already exists
    above the first placement (`min(p.y_in for p in placements)`, capped at `HEADER_MAX_IN=1.0`)
    — never a fixed height that could bleed into a design. `filename_hint` also becomes the S3
    `ContentDisposition` filename (`.png`/`.pdf`) via `storage.upload()`'s new
    `download_filename` param. The S3 *key* stays exactly as opaque as before — this only adds a
    header for callers/inspection tools, per wave.md's AC2 scope note.
  - **AC3.** `label_gap_in` replaces the hardcoded `LABEL_GAP_IN=0.04` (default now
    `DEFAULT_LABEL_GAP_IN=0.125`, matching the new contract default). A thin dashed cut guide
    (`render_cut_guide`) is drawn centered in the gap when there's room for one.
- `app/storage.py`: `Storage.upload()` gains `download_filename: str | None`; `S3Storage` sets
  `ContentDisposition: attachment; filename="..."` (quotes/CR/LF stripped); `LocalStorage`
  accepts and ignores it (dev/test has no header equivalent).
- `app/main.py` (narrow grant): `ComposeRequest` gains `label_gap_in` (default
  `compose.DEFAULT_LABEL_GAP_IN`) and `filename_hint`, passed through to `compose_sheet()`.
- Tests: `tests/test_compose.py` — pure-function module-floor test, the exact fail/succeed
  boundary (`test_compose_fails_loudly_when_label_strip_too_short`), QR decode at 150/200/300 DPI
  (`test_compose_qr_decodes_at_multiple_dpi`), header decode (`test_compose_header_decodes`), no
  header when `filename_hint` is omitted, cut-guide pixel check, plus the existing
  `test_compose_small_sheet` updated for the new floor (see gap below).
  `tests/test_storage.py` — `ContentDisposition` set/unset via moto. `tests/test_api.py` —
  `test_full_flow`'s `/nest`+`/compose` now share an explicit `label_height_in=0.8` and exercise
  `filename_hint` end-to-end.

**invai-contracts** (commit `ba59371`)
- `src/schemas/vendors.ts`: `SheetSpec.labelGapIn = z.number().nonnegative().default(0.125)`
  (exact architect diff from `wave.md`), `DEFAULT_SHEET_SPEC.labelGapIn = 0.125`. Nothing else in
  the file touched (kept clear of T-9-3's `PDF_MAX_LENGTH_IN`/`sheetSpecPdfCapError`, already
  committed as `2b2f12b` by the time I landed).

**invai-backend** (commit `00fb593`, granted: "backend sheet-spec pass-through")
- `src/db/schema/vendors.ts`: local `SheetSpec` type + `DEFAULT_SHEET_SPEC` mirror `labelGapIn`.
- `src/modules/production/sheets.ts`: `composeSheet()`'s `imaging.compose()` call now sends
  `label_gap_in: spec.labelGapIn`.
- `src/integrations/imaging/client.ts`: `compose()`'s input type gains `label_gap_in?: number` so
  the call above type-checks (needed for the excess-property check on the object literal).
  `filename_hint` was **not** added here — see gap below.

## Verification
- `invai-imaging`: `uv run ruff check . && uv run ruff format --check .` clean on touched files
  (one pre-existing, unrelated formatting issue in `app/labels.py`, not touched by me). `uv run
  pytest` — 51/51 passed (full suite, including T-9-1/T-9-3's concurrent work). Real run against
  `LocalStorage` for every new test (S3 `ContentDisposition` covered separately with `moto`).
  Peak RSS/time: scoped-down check (not the full 240in benchmark, given the change is small,
  local per-placement draws, not a change to the streaming architecture) — a 22x121.75in, 30-design
  sheet with PNG+PDF+preview and both new features active ran in 4.2s at 294MB peak RSS
  (`/usr/bin/time -l`), in line with the README's existing budget table for a sheet at roughly
  half the length and a third the design count.
- `invai-contracts`: `pnpm typecheck` and `pnpm test` clean (31/31).
- `invai-backend`: `pnpm typecheck` clean repo-wide; targeted `biome check` clean on the 3 touched
  files. No dedicated test file exists yet for `sheets.ts`/`client.ts`'s compose path (not added —
  outside this card's owned paths).

## AC1 finding — escalate: current defaults can't satisfy the 0.5mm floor at all
The 0.5mm/module requirement is pure geometry: `available_label_height_in >= n * 0.5mm`, where
`n` is the QR's module-grid size (border included) — **independent of DPI**. The smallest
possible QR (version 1, `n=23` with a 1-module quiet zone) already needs **>= 0.45in** of label
content height, for *any* transfer_id, however short. `label_height_in`'s shared default is
**0.35in** everywhere it's set (imaging `NestRequest`/`ComposeRequest` `Field(0.35, ...)`,
backend `LABEL_HEIGHT_IN = 0.35` in `sheets.ts`) — none of which are in this card's owned or
granted paths. So **every real `/compose` call made with today's defaults will now 422** under
AC1's literal floor, not just edge cases.

I implemented the floor and the fail-loud behavior exactly as specified (wave.md's testability
note asks for a precise boundary, not "somewhere small"), and adjusted my own tests to pass an
explicit, larger `label_height_in` (0.8in) that clears the boundary with margin — but I did
**not** touch `NestRequest.label_height_in`'s default or backend's `LABEL_HEIGHT_IN` constant,
since neither is owned or granted to this card. Raising them is a coordinated cross-repo change
(imaging `NestRequest` + backend `sheets.ts`, both outside T-9-2) needed before AC1 can ship
without breaking every real gang sheet. Flagging for the tech lead — this needs either a T-9-2
follow-up with a wider grant, or a new wave-10 card.

## Other gaps
- `filename_hint` is implemented and tested in imaging, but backend's `composeSheet()` doesn't
  send one yet (only `label_gap_in`, per the explicit "sheet-spec pass-through" grant — a
  filename hint is sheet-instance data, not `SheetSpec` data, so it wasn't in scope). AC2's
  header/ContentDisposition won't appear on real sheets until a follow-up wires a constructed
  value (e.g. sheet name + order numbers) through `sheets.ts` and `client.ts`.
- Real sheets built with the current default 0.25in margin won't show a header QR even once
  `filename_hint` is wired up (same geometric floor as AC1, applied to the header's available
  top clearance) — the header is deliberately best-effort/blank in that case, never a failure.
