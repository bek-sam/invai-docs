# Report: T-A5 Inventory and design analytics
Author: backend-engineer (inventory) on Opus 5.5

Card: T-A5  Owner: backend-engineer (inventory)  Scope ref: `product/scope.md#mvp-in` items 6, 8
Owned (edit): `analytics/router.ts` (own 4 lines), `analytics/inventory-service.ts` (new),
`analytics/design-service.ts` (new), `analytics/*.test.ts` for these files, `inventory/reorder.ts`
(size-split addition)
Depends on: T-A2 (contract f466088, landed), T-A4 (router base, landed)

## Progress
- 2026-09-30 intake, read contract/spec/metric SQL/T-A3-T-A4 patterns; built inventory-service.ts,
  design-service.ts, export-service.ts, router.ts lines, reorder.ts size-split; fixed test seed
  bugs (SQL timestamptz cast, 365-day sale window, dead-stock consume gaps); full suite green;
  curl exercise on :3151; committed 85fa715; report final.

## Built
- `analytics.inventoryHealth`: on-hand value, turns (null under 90 days of InvAI history or
  onHandValue=0), dead stock (top 50 by value), size-mix gaps (per style×color, shown even under
  the 30-unit minimum with `hasEnoughUnits:false`), stockout exposure (files: `analytics/inventory-service.ts`)
- `analytics.supplierTrends`: unit cost and median lead days by supplier×style×month (min 3
  received POs/month), global measured lead days vs `inventory_settings.leadTimeDays`, suggests
  an update when they differ by >3 days (files: `analytics/inventory-service.ts`)
- `analytics.designLifecycle`: stage per design (dead→new→growing→declining→steady→inactive, per
  `design_lifecycle_stage.md`), overridden by the market module's own trend (rising→growing,
  falling→declining, flat→steady) when `getTrendSignal` returns anything but `insufficient`;
  never touches market's tables (files: `analytics/design-service.ts`)
- `analytics.export`: CSV per view for all 10 `analytics.*` reads, discriminated on `view`,
  reusing the `finance.exportCsv` S3/file pattern; calls T-A3/T-A4/this card's services read-only
  (files: `analytics/export-service.ts`)
- `inventory/reorder.ts` `splitBySizeCurve`: pure, proportional size split of a reorder quantity
  across sizes by trailing sales share (largest-remainder rounding so it sums exactly); proposes
  quantities only, writes nothing
- `analytics/router.ts`: added the 4 T-A5 registrations, removed the now-empty `stubRouter`
  fallback (all 11 `analytics.*` procedures are implemented)

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| AC-C1 (under-stocked size shown, <30-unit group shown not omitted) | yes | `inventory-service.test.ts` "size-mix gap: L under-stocked..." |
| AC-C2 (dead stock matches blank_stock_health.sql) | yes | same file, parity block "blank_stock_health.sql" |
| AC-C3 (size-split follows the curve, every line editable, nothing auto-submits) | yes | wired into `reorderSuggestions` (`inventory/service.ts`, grant 2026-09-30 02:05); `service.test.ts` "reorder size-curve split (AC-C3)" — see Follow-up below |
| AC-C4 (dead design overridden by market trend) | yes | `design-service.test.ts` "a market trend for the design wins..." |
| AC-C5 (supplier unit cost/lead days match SQL; suggestion past 3-day gap) | yes | `inventory-service.test.ts` "unit cost by month...", parity block "supplier_trends.sql" |
| AC-B/C-screen1 (hasEnoughHistory false for a brand-new shop) | yes | both test files, "hasEnoughHistory is false for a brand-new shop" |
| AC-E4 (tenant isolation) | yes | both test files, "tenant isolation" cases; ids never appear in JSON |
| AC-E5 (FORBIDDEN without finance.read) | yes | both test files + export-service.test.ts, router-level FORBIDDEN cases; live curl (designer 403 on all 4) |

## Checks I ran
| Repo | Command | Result (last lines) |
|---|---|---|
| invai-backend | `pnpm typecheck` | clean, no errors |
| invai-backend | `pnpm lint` (biome check .) | `Checked 440 files in 228ms. No fixes applied.` |
| invai-backend | `pnpm test` (own DB `invai_ta5_test`, `REDIS_URL=redis://localhost:6379/11`) | `Test Files 165 passed \| 2 skipped (167)` / `Tests 1291 passed \| 3 skipped \| 1 todo (1295)` |

## Exercised for real
- `PORT=3151 REDIS_URL=redis://localhost:6379/11 pnpm dev:api` on the shared dev DB (read-only)
- Signed in as `owner@desertbloom.test`; `GET /api/v1/analytics/inventory-health?days=90` → 200,
  real seed numbers (`onHandUnits:2281`, `deadStock.variants:21`, `turns:null` -- seed company is
  younger than 90 days, matching the documented rule)
- `GET /api/v1/analytics/supplier-trends?period[from]=...&period[to]=...` → 200, `rows:[]` (seed
  has no purchase orders yet), `leadTimeSettingDays:3`
- `GET /api/v1/analytics/design-lifecycle` → 200, real designs; one row shows
  `marketTrend:"flat"` from the market module's own signal, confirming the defer-to-market path
  fires on real data
- `POST /api/v1/analytics/export-csv {"view":"inventoryHealth","days":90}` → 200, `{"key":"..."}`
- Refused case: `designer@desertbloom.test` → 403 `FORBIDDEN {"permission":"finance.read"}` on
  `inventory-health`, `design-lifecycle` and `export-csv`

## Decisions
- `hasEnoughHistory` for `inventoryHealth`/`designLifecycle` follows T-A4's reviewed OR-of-any-
  metric-sample pattern (`operations-service.ts`), not a single company-tenure check, since
  AC-B/C-screen1 is phrased "below every metric's minimum sample overall" the same way for all
  three procedures. `turns` on its own still requires 90 days of company tenure per
  `blank_stock_health.md`'s own minimum-sample line, independent of the whole-response flag.
- Market trend override (AC-C4): a non-`insufficient` `getTrendSignal` reading replaces the
  computed `stage` (rising→growing, falling→declining, flat→steady), per the metric doc's caveat
  ("when both exist, the market trend wins and the stage says so"); wrapped in try/catch so a
  market-side glitch degrades to "no market trend" rather than breaking the whole response.
- `export`'s CSV shape for `unitEconomics`/`shippingMargin`/`leakage`/`profitBridge`/`breakEven`
  is a reasonable flattening of each read's rows/totals (T-A3/T-A4 own no canonical "export
  columns" of their own); `operations`'s export combines its several sub-tables under a `section`
  column since it has no single row list. These are engineering judgment calls, not ACs.
- No migration: this card adds no schema.

## Known gaps and follow-ups
- ~~`splitBySizeCurve` not wired into `reorderSuggestions`/`createPoFromSuggestion`~~ — closed by
  the grant extension; see "Follow-up (AC-C3 wiring)" below.
- `analytics.export`'s per-view CSV column choices for the 7 non-T-A5 views are a defensible
  flattening, not reviewed against a finished screen design (T-A7 hasn't built the UI yet); worth
  a look once the analytics screens exist.
- `supplierTrends` returns `rows:[]` on the current shared dev seed (no purchase orders seeded
  yet); AC-C5's real-data proof is the parity test against hand-seeded POs in
  `inventory-service.test.ts`, not the live dev DB.

## Blocked by other owners
- none

## Processes and data
- Stopped: API on :3151 (tsx watch PID 10378, node listener PID 10395) -- confirmed `lsof :3151`
  free. Full-suite run PID 10175 completed and exited. Dropped `invai_ta5_test`, flushed Redis DB
  11. Shared dev DB: untouched (only sign-ins and reads).

## Follow-up (AC-C3 wiring) — 2026-09-30 02:xx, backend-engineer (inventory)

Wired `splitBySizeCurve` (reorder.ts, commit 85fa715) into `inventory/service.ts`'s
`reorderSuggestions`, under the grant extension logged in `wave.md` "Grants" (2026-09-30 02:05:
owned paths extended to `inventory/service.ts` and `inventory/router.ts` + their tests, size-curve
wiring only). No `router.ts` change was needed: the wiring is entirely inside `reorderSuggestions`,
and `createPoFromSuggestion` already only ever creates an editable draft.

### Built
- `inventory/service.ts`: new private `splitPlanLinesBySizeCurve()` groups each supplier plan's
  lines by style x color, and for any group with 2+ orderable sizes (excluding a size the mock/
  live supplier currently reports zero stock for, same as `planReorder`'s own "don't order" rule)
  redistributes the group's existing total suggested qty across its sizes proportional to trailing
  daily velocity (`SizeShare.salesShare`), via `splitBySizeCurve`. A single-size group passes
  through unchanged. `reorderSuggestions` calls this before building the response, and recomputes
  each plan's `subtotal`/`meetsThreshold`/`shortfall` from the redistributed lines (unit cost can
  differ by size, so the total group qty being unchanged doesn't guarantee the dollar subtotal is).
  `createPoFromSuggestion` was already a thin wrapper over `createPo`, which always inserts
  `status: "draft"`; nothing in the reorder path calls `submitPo`.

### Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| AC-C3 (size-split follows the curve, every line editable, nothing auto-submits) | yes | `service.test.ts` describe "reorder size-curve split (AC-C3)": (1) "splits the group's suggested qty proportional to the trailing size curve, summing to the total" — a 3-size group with a 10/10/80% trailing velocity split gets suggested qtys 2/2/18 (vs. 3/3/16 if each size's own independent reorder point were used unmodified), summing to the same 22-unit total; (2) "creates an editable draft PO from the suggestion, and nothing submits it automatically" — `createPoFromSuggestion` returns `status: "draft"`; `updatePo` changes every line's qty on that same draft; `getPo` re-read still shows `draft`; only an explicit `submitPo` call moves it to `submitted` |

### Checks I ran
| Repo | Command | Result (last lines) |
|---|---|---|
| invai-backend | `pnpm typecheck` | clean, no errors |
| invai-backend | `pnpm lint` (biome check .) | `Checked 440 files in 404ms. No fixes applied.` |
| invai-backend | `vitest run src/modules/inventory/ src/modules/analytics/` (own DB `invai_ta5b_test`, `REDIS_URL=redis://localhost:6379/11`) | `Test Files 14 passed (14)` / `Tests 123 passed (123)` |

### Decisions
- The redistribution runs unconditionally on every 2+-size group in a supplier's plan (not only
  ones flagged with an explicit "size gap"): the contract's `ReorderSuggestion`/`ReorderLine`
  schemas (read-only, `invai-contracts`) have no field to carry a gap flag or an opt-in switch, and
  the spec's "gains an optional size split" (`business-analytics-v2.md` Track C) reads as "the
  suggestion optionally differs from the naive per-size math", not a new request parameter. A
  size with a genuinely proportional stock mix already gets a proportional split, so this is a
  no-op for a style/color with no gap.
- Free-freight top-up units (already summed into each line's qty by `planReorder` before this
  runs) are redistributed along with the rest of the group's total; they are not held back or
  applied after the curve split, since the contract has no separate "top-up" quantity field to
  preserve.
- No change to `inventory/router.ts` or `inventory/reorder.ts`: the pure `splitBySizeCurve`
  function from the original T-A5 commit needed no changes, and the router line for
  `reorderSuggestions` was already unconditional.

### Gotcha for the record
- Verifying this locally against a fresh scratch DB (`invai_ta5b_test`) failed at first with a
  cross-tenant `purchase_orders_location_id_fk` violation that looked like an RLS bug: pointing
  `TEST_DATABASE_URL` at the **owner** role (`invai`, which bypasses RLS as the table owner)
  instead of the **app** role (`invai_app`) let `defaultLocationId()`'s unfiltered
  `select ... from locations order by ... limit 1` return a different test company's location. Not
  a product bug — `TEST_DATABASE_URL` must use `invai_app:invai`, `TEST_MIGRATION_DATABASE_URL`
  the owner `invai:invai`, matching `CLAUDE.md`'s role split.

### Processes and data
- No API server started for this follow-up (service-level tests only cover AC-C3; the original
  report's live curl exercise already covered `reorderSuggestions`/`createPoFromSuggestion` as
  `owner@desertbloom.test`, unaffected in shape by this change). Test DB `invai_ta5b_test` dropped
  and Redis DB 11 flushed after the run. Shared dev DB: untouched. Commit: `6b531c2` "T-A5: wire
  size-curve split into reorder suggestions (AC-C3)".

## Round 2 (review r1 fixes)
Commit `b5ea7d0` (invai-backend), on top of 6b531c2. Files: `src/modules/inventory/service.ts` + `service.test.ts`, `src/modules/analytics/design-service.ts` + `design-service.test.ts`.

| Finding | Fix | Regression test (failed on 6b531c2, passes now) |
|---|---|---|
| 1 AC-C3 size split | `splitLinesBySizeCurve` (exported, pure) water-fills the group's position after the order (available + incoming + qty) along the size curve: each line = clamp(level x share - position, 0, supplierStock). Excess past a cap goes to sizes with room; if no size has room the group total shrinks. Lines keep input order (most-needed first, which also covers note 5's ordering remark). | `inventory/service.test.ts`: "never suggests more of a size than the supplier has" (before: L=53 with stock 40; now L=40 and S=M), "sizes that sell the same end at the same position" (before: end gap 20; now <= 1), "caps every line and shrinks the group total (pure)". The existing 2/2/18 split test is unchanged and green. |
| 2 AC-C4 trend | Only the design's own reading (`provenance.source === "own"`, not insufficient) sets `marketTrend` and the stage. Niche-level outside readings are ignored, so they never turn `dead` (or any stage) into another. | `analytics/design-service.test.ts`: "a niche-level reading never moves the stage" (niche google_trends "rising" on a dead design: before `growing`, now `dead` with marketTrend null). The own-trend test still wins (`dead -> growing`). |
| 3 AC-B/C-screen1 | A never-sold listed design is dead only once the shop has >= 60 days in InvAI (`companies.created_at` to `asOf`, the same tenure source as `inventoryHealth`); before that it falls to `inactive`. `hasEnoughHistory` = 60+ days in InvAI, or some design with >= 3 units in 365 days (the metric's minimum sample). | "a brand-new shop with listings and no sales" (3 listings, no sales: before hasEnoughHistory true and 3 dead; now false and none dead; after backdating created_at 61 days: true and all dead). |
| Note 5 swallowed error | The market read runs in a savepoint (`tx.transaction`), so a failure rolls back only itself and the outer transaction stays usable; the failure is logged (`analytics.design`, companyId, designId), not hidden. N+1 left as is (skipped per brief). | covered by the existing lifecycle tests |

Checks (own DB `invai_ta5c_test`, app role `invai_app`, migration role `invai`, `REDIS_URL=…/11`; dropped and flushed after):
- `pnpm typecheck` exit 0; `pnpm lint` → `Checked 441 files … No fixes applied.`
- `vitest run src/modules/inventory/ src/modules/analytics/` → 14 files, 128/128 passed.
- Before-fix proof: HEAD 6b531c2 in a scratch git worktree with the new test files → the 5 new tests fail (`expected 53 to be 40`, `expected 20 to be less than or equal to 1`, `splitLinesBySizeCurve is not a function`, stage `growing` instead of `dead`, `expected true to be false`). Worktree removed.
- Not re-exercised with curl this round (service-level fixes, covered by the tests above). T-A1's seed edits left untouched and unstaged. Not pushed.
