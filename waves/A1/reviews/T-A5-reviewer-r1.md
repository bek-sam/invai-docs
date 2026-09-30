Verdict: changes-required
# Review T-A5 r1 — reviewer (Opus 5.5); author backend-engineer (inventory), report says Opus 5.5 (card: sonnet; same model as me, tenancy co-review is security-reviewer on sonnet). Commits 85fa715, 6b531c2.

## Evidence I re-ran (own DB `invai_rv6_test`, app role `invai_app` / migration role `invai`, `REDIS_URL=…/12`; dropped + flushed after)
- `pnpm typecheck` exit 0; `pnpm lint` → `Checked 441 files … No fixes applied.`
- `vitest run src/modules/analytics/ src/modules/inventory/ src/api/authz.test.ts src/db/rls-coverage.test.ts` → 16 files, 137/137 passed.
- analytics T-A5 files (inventory/design/export-service.test.ts) 2 more runs → 34/34 each (no tie flake).
- `scan-test-weakening.sh invai-backend 2e564af` → 0 removed / 110 added assertions; one `toBeTruthy` (inventory-service.test.ts:567) is followed by value checks: fine.
- Scratch probes (git archive HEAD and 85fa715 in scratchpad, deleted): see findings 1–3. No API started (not needed); shared dev DB read-only (`market_signals`, `market_design_niches` counts).
- Author's full suite on a shared DB: does not weaken evidence here; my isolated targeted run is green and the diff touches no shared code (`src/lib`, `src/db`, `src/api`).

## Acceptance criteria
- AC-C1 met (gap shown per size; <30-unit groups kept with `hasEnoughUnits:false`, `gapPts:null`, consistent with AC-B/C-screen1).
- AC-C2 met (parity block runs `blank_stock_health.sql`; service mirrors it). AC-C5 met (parity vs `supplier_trends.sql`, >3-day suggestion; `avgUnitCost` fractional cents per T-A2 ruling).
- AC-C3 **not met as built** (finding 1): draft-only / no auto-submit is proven, but the curve split breaks the supplier-stock cap and can create a size gap.
- AC-C4 **partly met** (finding 2): own-trend override works, but niche-level (mock) readings also override, so a dead design shows "growing".
- AC-B/C-screen1: inventoryHealth met; designLifecycle **not met** (finding 3).
- AC-E4/E5 met: every query filters `company_id` under `withTenant`; isolation + FORBIDDEN tests pass; authz/rls-coverage green.

## Checks
- Market data only via `getTrendSignal` (market/service.ts export); no market tables in service code (tests insert signals via `withSystem`: test-only, fine).
- `export` returns `{ key }` like `finance.exportCsv`, reads T-A3/T-A4 services only, writes no table; CSV formula guard in `lib/csv.ts`.
- Router diff: only the 4 T-A5 registrations + imports, `stubRouter` spread removed; T-A3/T-A4 lines untouched.
- Tiebreaks: dead stock, stockout, design rows, size groups, supplier rows (SQL `order by 1,2,3`) all deterministic.
- Money integer cents except accepted `avgUnitCost`; no migration; no PII; single-size groups pass through unchanged (code path `orderable.length < 2`).

## Findings
1. **Blocking — correctness (AC-C3).** `inventory/service.ts:815-821` redistributes the group's qty by velocity alone, dropping `baseSuggestion`'s `min(qty, supplierStock)` cap and ignoring current stock. Probe (G-style, S/M vel 5, L vel 10, mock L supplier stock 40): before 6b531c2 L=40, S=M=95; at HEAD **L=115 with supplierStock 40**, S=57, M=58 — suggests ordering 75 shirts the supplier does not have. Second group (S avail 20, M avail 0, equal sales): before S 75→95, M 95→95; at HEAD S 85→105, M 85→85 — the split *creates* a size gap between two sizes that sell the same. Fix: split the target position (available+incoming+qty) by the curve, clamp each line at supplierStock and redistribute the excess; add tests for both cases.
2. **Blocking — correctness (AC-C4).** `analytics/design-service.ts:139-144` lets any non-`insufficient` `getTrendSignal` reading win, and that function falls back to the design's *niche* outside sources (market/read.ts:88). Probe: listed design, last sale 2026-01-01, own trend absent, mock `google_trends` niche reading "rising" → stage `dead -> growing`. Dev DB: all 40 design own trends are `insufficient`, 34/40 designs have niches with mock niche trends, so the report's `marketTrend:"flat"` row is a niche mock, not a design trend. Fix: defer only when the winning reading is the design's own (`subjectType design`/`source own`), or at least never over `dead`; test it.
3. **Blocking — AC-B/C-screen1 / metric caveat.** `analytics/design-service.ts:54-55,183`: a never-sold listed design is `dead` regardless of shop age, and `hasEnoughHistory = rows.length > 0`. Probe: brand-new shop, 3 imported active listings, no sales → `hasEnoughHistory=true`, all 3 `dead` ("retire everything" on day 1). `design_lifecycle_stage.md` caveat: never-sold counts as dead only after 60 days of InvAI history; the 3-unit floors are the minimum sample.
4. Low — ownership: `analytics/export-service.ts` + `.test.ts` are outside the card's owned files and the wave file split (the card promises `export` but names no file). Needs a tech-lead grant like T-A3's `finance-testkit.ts`; no code change asked.
5. Optional: `getTrendSignal` per design is N+1 (~4 queries/design); the `catch` at design-service.ts:145 swallows a DB error inside the tx (later queries then fail silently); plan lines now come back in group order, not most-needed-first.
