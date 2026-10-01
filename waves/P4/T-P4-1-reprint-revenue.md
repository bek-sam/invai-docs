# T-P4-1: A reprinted item stays a sale unit: profit keeps its revenue, re-import never adds a second unit (B-242)

| Field | Value |
|---|---|
| Wave | P4 |
| Scope ref | `always-in-scope: bug` (profit shows $0 revenue and a false loss on reprinted orders; re-import after a reprint can add a second unit to ship, `product/scope.md`) |
| Spec | backlog B-242; `waves/P3/reports/T-P3-4.md`; ruling `decisions/0020-is-reprint-means-re-pressed.md`; `reviews/plan-architect.md` |
| Owner | backend-engineer (finance, orders, analytics, market; one role across modules) |
| Reviewer | reviewer (fable) |
| Co-reviewers | architect (opus): cross-module meaning of `isReprint` |
| Risk flags | money, floor-correctness (never double-ship) |
| Model | opus |
| Depends on | the P3 close-out push. T-P4-4 (ai) and T-P4-5 (QA fixtures) land the same day; the gate runs only when all three are approved |

## Ruling (decision 0020, architect plan review)
1. `isReprint` on `order_items`, `profit_lines` and `transfers` means "re-pressed at least once". It is informational and never decides whether a unit is a sale. A sale unit is any non-cancelled item (analytics may still exclude refunded lines). `openReprint` stays as it is. Reprint cost is already in the transfer cost (`finance/service.ts:691`, every transfer for the item).
2. Re-import double-creates today: `orders/import.ts:533` drops reprinted units, so (case 1) a line whose only unit was reprinted is treated as a new line and gets a second unit, (case 2) a 2-unit line with one reprint gets a replacement unit, and (case 3) a channel line-cancel (`:872`) skips the reprinted unit, so that shirt still ships. Fix: drop the `isReprint` filter at `:533,688,872`.
3. No backfill job: `profit_lines` is a per-item upsert. The gate reseed fixes the seed, `finance.nightly` recomputes 45 days, and `finance.recompute` covers older ranges. Add one line to the report for release notes.
4. No migration, no seed, schema or contract change.

## Owned paths (edit)
- `invai-backend/src/modules/finance/service.ts` (`recomputeProfit` sellable `:605`, order summary `:1034-1036`), `src/modules/finance/refunds.ts` (`:143,148,272`), and their tests
- `src/modules/orders/import.ts` (`:533,688,872`) and `src/modules/orders/import*.test.ts`
- `src/modules/analytics/shared.ts` (`:61`), `analytics/finance-service.ts` (`:158,212,549-586`), `analytics/design-service.ts` (`:129`), `analytics/inventory-service.ts` (`:167`), `analytics/finance-testkit.ts` (rewrite the `:356` sibling revenue-0 line to the real model: the same item re-pressed, with a second transfer), `analytics/*.test.ts`
- `src/modules/market/history.ts` (`:60,99`); `src/modules/digest/digest.test.ts` (`:350` fixture only)

## Read-only paths
- `src/modules/production/**` (no change), `src/ai/**` and `src/modules/ai/**` (T-P4-4), `src/modules/market/market.acceptance.test.ts` and `src/modules/digest/digest.acceptance.test.ts` (QA, T-P4-5), `src/db/**`, `src/test/**`, every other module, `invai-contracts/**`, `invai-web/**`, `invai-floor/**`

## Acceptance criteria
1. Given a 2-item order, when one item fails QC and is reprinted, then its profit line keeps that item's sale revenue (unit price − discount share + shipping share − tax inside), the order counts 2 units, and the second transfer's cost is added; CM2 drops only by the reprint's cost.
2. Given a 2-item order where both items are reprinted, then `analytics.losingOrders` shows units 2 and the order's sale revenue (not 0), and lists the order only if the reprint costs really make it lose money.
3. Re-import (orders tests): after a reprint, re-importing the same payload gives the same item count and an empty `changed` list, for a quantity-1 line and for a quantity-2 line with one unit reprinted; a channel line-cancel cancels the reprinted unit too.
4. Tests for orders without reprints pass unmodified. Tests whose fixtures used the sibling-row model are rewritten to the real model, and the report lists each one (this corrects a fixture; it never loosens an assertion).
5. Tenant isolation: everything stays under `withTenant`; the existing tenancy tests pass.
6. Re-import on the dev seed: one reprinted order's mock payload (or CSV) sent twice leaves its item count unchanged (read-only check of counts before and after; no reset).

## Verification
- While building: only the finance, orders, analytics, market and digest test files you touch (foreground). Once at the end: `pnpm typecheck && pnpm lint && pnpm test 2>&1 | tail -n 40` in `invai-backend`. At most 2 heavy test runs on the machine at once (RAM): don't start the full suite while the gate runs.
- Exercised: own API `PORT=3140`, `REDIS_URL=redis://localhost:6379/13`; on a scratch fixture shop, press, fail QC and reprint one item through the floor procedures, then call `analytics.losingOrders` and the profit summary as `owner@`; revenue and units in the report. Refused case: `presser@` → FORBIDDEN on `analytics.losingOrders`.

## Rules
- Role file `.claude/agents/backend-engineer.md`; `team/agent-brief.md`. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/backend-engineer/`.
- Commit only your paths, attribution line at the end. **Don't push; only the tech lead pushes after the gate.** Record PIDs, stop them, flush Valkey DB 13. Never reset the dev DB. Run tests in the foreground; don't end your turn while a test run is still going.
- Report (≤ 60 lines) to `invai-docs/waves/P4/reports/T-P4-1.md`, one progress line per milestone.
