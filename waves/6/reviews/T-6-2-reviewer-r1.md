# Review of T-6-2 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: (unattributed in report) on sonnet
- Verdict: **changes-required**

## Evidence I re-ran
Reviewed only this card's commits, each in its own worktree pinned to that exact SHA (detached
HEAD), isolated from later wave-6/7 commits sharing the same repos:
`invai-contracts` `b8f6eb5`, `invai-backend` `3b08f5a`, `invai-web` `c130bde`, `invai-imaging`
`a773566`+`896163a`, `invai-floor` `468d455` (floor and imaging were already at HEAD, no
worktree needed there). Backend and web needed their own `node_modules` (per-entry symlinks,
never the shared repo's `node_modules/@invai/contracts` symlink itself) with `@invai/contracts`
re-pointed: backend to a contracts worktree at `9de22ce` (the real contracts state live when
`3b08f5a` was authored — see note below), web to the live `invai-contracts` (`7bb2bb1`, same
reasoning). All worktrees and their node_modules were removed at the end.

| Command | Result |
|---|---|
| `invai-contracts`: `tsc --noEmit` / `biome check .` / `vitest run` | pass / pass / 4 files, 31 tests |
| `invai-backend`: `tsc --noEmit` | pass (after pinning contracts to `9de22ce` — see note) |
| `invai-backend`: `biome check .` | pass, no fixes |
| `invai-backend`: `vitest run src/modules/production` (own DB `invai_test_t62r`) | 5 files, 36 tests |
| `invai-backend`: `vitest run` (full suite) | 72 files, 505 tests passed — no regressions |
| `invai-web`: `tsc --noEmit` (worktree pinned at `c130bde`) | 1 pre-existing, unrelated error — see note |
| `invai-web`: `tsc --noEmit` at live HEAD (`c130bde` + T-6-3's `f2ef447` + later) | pass — confirms they build together |
| `invai-web`: `biome check .` / `vitest run` / `vite build` (worktree) | pass / 14 files, 76 tests / builds |
| `invai-web`: `vite build` at live HEAD | builds (same pre-existing >500kB chunk warning) |
| `invai-imaging`: `uv run ruff check .` | all checks passed |
| `invai-imaging`: `uv run pytest` | 30 passed |
| `invai-floor`: `tsc --noEmit` / `biome check .` / `vitest run` / `vite build` | pass / pass / 8 files, 86 tests / builds |
| `scan-test-weakening.sh` on each repo, scoped to this card's commit only | no hits in contracts, backend, web, floor |
| `print-bins.test.ts` copied onto `3b08f5a~1` (base) and run in isolation | all 7 fail (`createBin`/`markSheetPrinting`/`reprintReasonsByWeek` not a function) — proves the tests exercise the new code |
| Real pass on DB copy `invai_t62r_copy` (API :3193, imaging :8193, `REDIS_URL` db 11), signed in as `owner@desertbloom.test` | see criteria table and blocking finding |

**Note on the backend `tsc` pin:** the wave's contract stubs for T-6-2/T-6-3/T-6-4 land in
`invai-contracts` across three separate commits (`b8f6eb5`, `9de22ce`, and wave 7's `7bb2bb1`),
but `invai-backend`'s own commit right before this card's (`03eff41`, "NOT_IMPLEMENTED handlers
for wave 6 contract stubs T-6-2/3/4") already references `ai.exportCsv`/`finance.exportCsv`,
which only exist as of contracts' `9de22ce`. Pinning contracts at T-6-2's own commit (`b8f6eb5`)
alone therefore fails `tsc` with two unrelated errors; pinning at `9de22ce` (the real contracts
state live when backend's `3b08f5a` was authored, confirmed by commit timestamps) is clean. Not
a T-6-2 defect — the same cross-repo-ordering artifact the T-6-1 review already logged.

**Note on the web `tsc` pin:** isolating `c130bde` alone (even against live contracts) still
shows one error in `src/features/orders/order-actions.tsx:79` (`FlagCode` missing
`channel_edit_after_press`). Contracts' `7bb2bb1` (wave 7, adds that enum value) was authored at
18:51:55, one minute before web's `c130bde` at 18:52:37 — so the live web repo already needed it
by the time T-6-2 was built, but the fix (`b93f554`) landed in a later, unrelated commit. T-6-2
never touches `order-actions.tsx` or that file's `FlagCode` map. Confirmed non-blocking: `tsc` at
today's live `invai-web` HEAD (which includes both `c130bde` and `b93f554`) is clean.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. In-house printing (`ready → printing → printed`, vendor path unchanged) | **no — see blocking finding** | The happy path works: with `printsInHouse` true, `markPrinting` moved a `ready` sheet to `printing` (403 `FORBIDDEN` confirmed when false), then `markPrinted` moved it to `printed`. `SHEET_STATES`/`SHEET_TRANSITIONS` match `wave.md` exactly (`printing` between `ready`/`printed`). **But** `markSheetPrinted` (`invai-backend/src/modules/production/sheets.ts:1109`) has no guard at all — no `printsInHouse` check, no check that the sheet is currently `printing`. Since `printed` is already a valid `SHEET_TRANSITIONS` target from `sent` and `acknowledged` (the vendor states), I called `POST /production/sheets/{id}/mark-printed` directly on a real vendor-flow sheet (`#25`, vendor "Sun City DTF", status `sent`, company `printsInHouse: false`) and it succeeded, flipping straight to `printed` with a stamped `printedAt` — no vendor confirmation, no `printing` state, no `FORBIDDEN`. The vendor path is **not** unchanged: this card adds a new, ungated way to fabricate a vendor sheet's completion. |
| 2. Reprint queue (list, filters, cancel, `reasonsByWeek`) | yes | `reasonsByWeek` verified live against real seed reprints (`weekStart`/`total`/`byReason`, cancelled excluded, matches backend test). List/filter/cancel UI reuses the pre-existing, already-tested `reprints.list`/`cancelReprint` (unchanged by this card); route wiring and en/es read cleanly. |
| 3. Bins (list/create/rename/archive, `BIN:`/`B:` labels via `files.downloadUrl`) | yes | Live: created bin `REVA1`, renamed, archived (dropped from the default list, `includeArchived` brings it back), `bins.labels` returned an S3 key, downloaded the PDF from MinIO and decoded its QR with `pypdf` + `zxingcpp` → `'BIN:REVA1'` exactly, on a 288×432pt (4×6in) page. `BIN_OCCUPIED` on archive is covered by the backend test (not re-tried live). Blank (`B:`) labels share the same imaging path/tests; not separately re-tried live (T-6-1's endpoint, unchanged here). |
| 4. Quality (en/es, 390px, keyboard) | yes | en/es key sets diff identically (77 keys each side, no mismatch); no hardcoded English JSX literals found in `bins.tsx`/`reprints.tsx`; both routes use the shared, already-audited `DataTable`/`Dialog`/`Field`/`NativeSelect` components with `aria-label`s on icon-only buttons. Not independently re-tested live at 390px/keyboard — relying on shared components plus the code read, same as prior wave-6 reviews. |

## Blocking findings
1. **`invai-backend/src/modules/production/sheets.ts:1109`** (`markSheetPrinted`, wired at
   `invai-backend/src/modules/production/router.ts:37`) — a vendor-path sheet can be forced
   straight to `printed` through the new `production.sheets.markPrinted` procedure, with no check
   that the company prints in-house and no check that the sheet is currently `printing`.
   Failure scenario: an office user at a vendor-only shop (or any shop where `printsInHouse` is
   false) calls `production.sheets.markPrinted` on a sheet that's `sent` or `acknowledged` (both
   valid predecessors of `printed` in `SHEET_TRANSITIONS`) — confirmed live against a real vendor
   sheet — and the sheet is marked `printed` and stamped, without the vendor ever having
   confirmed the print or the transfers being cut. Downstream, `markSheetReceived` then treats
   those units as legitimately printed and moves them to the floor. Fix: `markSheetPrinted`
   needs the same `companyPrintsInHouse` guard `markSheetPrinting` already has (or, at minimum,
   assert `sheet.status === "printing"` before transitioning), so the endpoint can't be reached
   from a vendor-path state.

## Checks
- [x] Only owned paths changed (`git diff --stat`): contracts touches only `contract/production.ts`,
  `schemas/production.ts`, `states.ts`; backend touches only `modules/production/**` + one additive
  migration; web touches `features`/`routes` under `production/**` + `i18n/{en,es}.ts` + `lib/nav.ts`
  + generated `routeTree.gen.ts` (the nav/route-tree hunks are shared with T-6-3's `f2ef447`, which
  supplies the actual ad-spend/profit source those hunks reference — confirmed both commits build
  together at live HEAD, see evidence table); imaging touches only `app/labels.py`, `app/main.py`,
  its own tests; floor touches only `src/api/demo.ts` (an explicit tech-lead grant per the report).
  `printsInHouse` itself was correctly landed by T-6-5 (`e14240a`/`1b72441`), not this card, per the
  wave's grant recommendation.
- [x] Nothing outside scope: no unrelated refactors found.
- [x] Tests exercise the behavior, and none were weakened: `scan-test-weakening.sh` found no hits in
  any of the five repos, scoped to this card's own commits. `print-bins.test.ts`'s 7 cases all fail
  against pre-T-6-2 code (confirmed above), proving they exercise the new behavior — but see the
  blocking finding: **no test calls `markSheetPrinted` from a `sent`/`acknowledged` state**, which
  is exactly the gap that let the bug through.
- [ ] Tenancy (`withTenant`, RLS on new tables), idempotency, money in cents, en/es text: tenancy
  and RLS are fine (no new tables; `bins.name`/`archivedAt` are additive columns on an
  already-RLS'd table; every new service function runs inside `withTenant`). Money doesn't apply
  here. En/es text is complete. **State-machine safety does not hold** — see blocking finding — so
  this box is unchecked overall even though the individual tenancy/RLS/money/i18n items are clean.
- [x] Decisions recorded where needed: the report's three flagged decisions (no `printed → received`
  branch needed, `Bin.id` added beyond the wave.md stub snippet, reasons report as a table not a
  12-series chart) are all reasonable and correctly reasoned; no objection.

## Optional notes (not blocking)
- The report claims 6 screenshots taken; none exist anywhere under `invai-docs/waves/6/` or
  elsewhere on disk (same gap the T-6-1 review already logged for that card — apparently systemic
  this wave, not specific to this author). I did my own real pass on a DB copy instead and reached
  the same outcomes the report describes for bins/reprints; only the printing-state gap above was
  new.
- No new frontend unit tests were added for the two new routes (`bins.tsx`/`reprints.tsx`) or the
  sheet-detail changes, despite ~680 new lines of route logic. Matches this repo's existing
  convention (T-6-1 added none either), so not blocking, but real coverage here is only the DB-copy
  browser/API pass, which won't run again after this review.
- `imaging`'s `/labels/qr` `caption` field has no `max_length` in its Pydantic model (unlike `code`,
  which is bounded 1–200). Low severity — only the trusted backend calls this endpoint, and its
  actual callers already bound `name`/`caption` upstream (`Bin.name` ≤ 80 chars) — but worth
  tightening for defense in depth. Detailed in the imaging-engineer co-review.
