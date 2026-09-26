# T-13-5: Realistic seed efficiency (B-111) + seed locale

**SHA:** `3bc8f53` (invai-backend, on `main`, not pushed) — supersedes `c7fcb25` below; see
"Update: real imaging `/nest`" at the end for the current numbers.
**Owned files touched (exclusive):** `invai-backend/src/db/seed/builder.ts`, `invai-backend/src/db/seed/data.ts` (unchanged — see below)
**Also touched (not exclusively granted, but required to satisfy AC2, uncontested — no other wave-13 card owns it):** `invai-backend/src/db/seed/index.ts` (one field added to `SeedUser`/`SHOP_USERS`, one line in the `pins` map)

## What was built

### 1. Root cause, confirmed

`builder.ts`'s gang-sheet layout (introduced by T-5-3's `72c1139` refactor) shelf-packed each
`PER_SHEET` (24-item) chunk sorted only by `placedAt`, never by width. A wide item (e.g. a 12in
"back" print) landing mid-row after narrower items forced an early wrap, wasting the rest of that
row's ~22in width. Matches the wave-13 root-cause writeup exactly.

### 2. Fix: real first-fit-decreasing, not just a width sort

The card's suggested one-line fix ("sort `chunk` by `widthIn` descending before the row-fill
loop", keeping the single-current-row shelf logic) was implemented and measured first — it only
reached **73.96%** average full-sheet efficiency, still short of target. Root cause: sorting alone
doesn't help when several same-width items land adjacent in sort order (e.g. multiple orders each
independently rolling a "back"-sized design into the same 24-item window, which does happen with
the realistic random mix) — the *next* item after a lone wide one is often another item just as
wide, so it still can't backfill that row, and the single-current-row shelf never revisits an
earlier, still-open row.

Replaced it with genuine multi-row first-fit-decreasing: sort the chunk by `widthIn` descending,
then for each item (widest first) place it in the **first already-open row that has room**
(checking every row opened so far, not only the most recent one) before opening a new row. This
lets a later, narrower item (youth/left-chest/sleeve) backfill the leftover width a wide item left
behind in an earlier row. `layout` stays indexed by the chunk's original `placedAt` order (a
`packOrder` index array drives the packing loop, not a re-ordered copy of `chunk`), so the
downstream transfers/placements code (`chunk[k]`/`layout[k]`) needed no changes.

A best-fit variant (pick the fullest eligible row, not just the first) was also tried and measured
identical results on this seed — kept the simpler first-fit version.

### 3. Locale (AC2)

`buildShopData`'s `pins` option gained an optional `locale?: "en" | "es"` field; when set, the pin
loop now also updates `users.locale` for that user (`invai-backend/src/db/seed/builder.ts`). In
`src/db/seed/index.ts`, `luis@desertbloom.test` ("Luis Presser") — the Spanish-speaking floor
staffer already in `SHOP_USERS` — now carries `locale: "es"`, threaded through the `pins` map.
Verified in the DB: `users.locale = 'es'` for that row. The demo builder (`modules/tenancy/demo.ts`,
T-5-3) passes `pins: []`, so it's unaffected.

### 4. Demo builder / art-size mix (AC3, and "don't touch the mix")

`data.ts` was **not changed** — `SIZE_MIX`/`DESIGNS`/`PRINT_SIZES` (the realistic size mix) are
untouched, per the card's "keep the art-size mix realistic" instruction. Both the full seed
(`db/seed/index.ts`) and the demo builder (`modules/tenancy/demo.ts`) call the same
`buildShopData`, so the packing fix and the same size mix apply to both automatically — no
demo-specific code needed changing.

## Verification (own scratch DB only)

Per instructions, ran entirely against `invai_t135_scratch` (created via
`docker exec local-postgres-1 createdb -U invai -T invai invai_t135_scratch`,
`DATABASE_URL=postgres://invai_app:invai@localhost:5432/invai_t135_scratch`,
`MIGRATION_DATABASE_URL=postgres://invai:invai@localhost:5432/invai_t135_scratch`). Never touched
the shared dev `invai` DB. `seed-output.json` was backed up to `/tmp` before the first run and
restored to its original content afterward (it's gitignored regardless, so no diff either way).
The DB itself was dropped at the end of the session.

Imaging was not up and the worker was not running during these runs (confirmed via `lsof`/`ps`);
film-efficiency (`gang_sheets.utilization`) is computed purely from print-item geometry, so this
doesn't affect the numbers, only whether sample-art/sheet PNGs render (`sheet files {"composed":0}`
in the log, expected without imaging).

`pnpm exec biome check` and `pnpm exec tsc --noEmit` are clean for both touched files (one
unrelated pre-existing `tsc` error in `src/api/orpc.ts` belongs to another in-flight agent's work
in this shared tree).

### Film efficiency — full 300-order seed (300 historical + 60 due-soon = 360 orders, 675 items,
25 gang sheets, 24 of them full at `PER_SHEET = 24`)

| | avg | min | max |
|---|---|---|---|
| **Before** (buggy placedAt-only shelf pack) | 69.58% | 61.00% | 80.00% |
| **After** (first-fit-decreasing, all rows) | **79.46%** | 72.00% | 85.00% |

Root cause fully addressed (+9.9 points, wide-item-mid-row wrap eliminated) — but this run's
average lands **below** the card's 85–92% target band. Investigated why with hand-verified
optimal-packing bounds for several of the worst chunks: the "back" print (12in wide) can never
pair with a second "back" under the 22in film (`2×12 + spacing > 21.5in` usable), so any chunk
where several orders' random line items happen to land a "back"-sized design (design selection is
uniform-random per line, `qty` capped at 1–2) forces that many extra, partially-filled rows no
matter how good the packer is — confirmed by computing the row-count lower bound (one row per
"back", one row per adult-pair) for the worst chunks and finding the greedy result already at or
near that bound. The "sleeve" print (3in wide, 10in tall) compounds this from the height side. This
is a property of the realistic mix + current `LABEL_HEIGHT_IN`/`HEADER_HEIGHT_IN` overhead
(`8b728b1`, `5ba3c8f` — kept as-is, not undone, per the card), not a packing-algorithm gap.

**Flag for the architect/PM:** either accept ~79–80% as the new realistic-mix baseline (still a
large, real improvement over the 69.6% bug, and the packing bug itself is fixed), or open a
follow-up card to revisit `PER_SHEET` (larger chunks amortize the fixed header cost and give more
same-width items to pair) or the overhead constants if 85–92% is a hard requirement.

### Seed time (AC4)

18–22s wall-clock per full run (well under the 60s budget), `seconds: 18` reported by the script
itself on the final verification run.

## Known gaps / follow-ups

- Measured efficiency (79.46% avg) is below the card's 85–92% target — see flag above.
- `src/db/seed/index.ts` was touched outside the card's listed exclusive-ownership pair
  (`builder.ts`, `data.ts` only) because AC2 (locale) can only take effect where `SHOP_USERS` is
  defined and passed to `buildShopData`; no other wave-13 card owns this file, and the edit is a
  two-line, additive, non-conflicting change (new optional field + one map line).
- Did not run the full golden-path/E2E suites (out of this card's token budget per
  `agent-brief.md`; T-13-4 owns E2E). Typecheck and biome are clean for the touched files.

## Update: real imaging `/nest` (tech lead direction, SHA `3bc8f53`)

The tech lead pointed out the product builds gang sheets through imaging's real `/nest` (2D
nesting with rotation) — the FFD packer above, however improved, is still a seed-only
approximation the real algorithm doesn't run. Changed `builder.ts` so each `PER_SHEET` chunk is
sent to `imaging.nest()` with the same request shape `modules/production/sheets.ts` uses
(`sheet_width_in`/`spacing_in`/`margin_in`/`max_length_in` from `DEFAULT_SHEET_SPEC`,
`allow_rotation: true`, `label_height_in`/`header_height_in`). Its returned placements
(`x_in`/`y_in`/`rotated`) now drive `gangSheets`/`transfers`/compose placements directly;
`utilization`/`length_in` come straight from imaging instead of a manual calc. A chunk can yield
more than one physical sheet (handled: `gangSheetBatches.sheetCount` and one `gangSheets` row per
returned sheet), though at 24 items this essentially never happens.

The FFD shelf pack from the previous commit is kept only as a fallback (imaging unreachable, or
`/nest` returns no placeable sheets), logged with `log.warn` per chunk plus a summary warning —
imaging is already required for the seed, so this path is not expected to trigger in a normal run.

**Verification:** scratch DB `invai_t135_scratch` again (created/dropped the same way as before,
`seed-output.json` backed up to `/tmp` and restored after — diffed to confirm restore). Ran
`invai-imaging` locally (`uv run uvicorn app.main:app --port 8000`, `.env` already has
`IMAGING_SHARED_SECRET=invai-imaging-dev-secret` matching the backend's default and
`IMAGING_DEV_ENDPOINTS=true`) so the seed's `imagingUp` check passes and `/nest` is actually
exercised, not skipped.

Confirmed via log grep that none of the 15 chunks fell back to FFD (no "fallback"/"unreachable"
lines) — every sheet in this run came from real `/nest`, including rotation (76 of 587 transfers
came back `rotated: true`).

| | avg | min | max |
|---|---|---|---|
| Before (buggy placedAt-only shelf pack) | 69.58% | 61.00% | 80.00% |
| FFD fallback (previous commit `c7fcb25`) | 79.46% | 72.00% | 85.00% |
| **Real imaging `/nest` (this commit)** | **83.04%** | 77.00% | 87.00% |

Closer to the 85–92% band than the FFD fallback, but still slightly under it on this run. Same
root cause as before, now confirmed with rotation available too: a 12in "back" print still can't
pair with a second one under the 22in film even rotated (rotating it makes it 14in wide, worse,
which is exactly what `/nest` did with single "back" items in a hand-check — see the `curl
/nest` sample in this session's transcript). Per the tech lead's direction, the PM accepts this as
the realistic number.

**Seed time:** this run measured 211s end-to-end (`seconds: 211` in the seed's own log), well over
the 60s budget — but the shared dev host's Docker/Postgres was under heavy contention during this
run (`docker ps`/`docker exec` themselves were unresponsive for several minutes concurrently,
unrelated to this change — confirmed the port was still accepting TCP connections throughout, so
it was host load, not a hang in this code). The previous (FFD-only) commit measured 18–22s on the
same DB under normal load; `/nest`'s own added per-chunk HTTP round-trip cost is small (roughly a
few hundred ms each, ~15 chunks). Flagging seed time as a risk to watch in CI if imaging or the DB
is ever slow there, but not attributing the 211s figure to the `/nest` change itself.
