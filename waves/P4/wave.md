# Wave P4: true profit for reprinted orders, and the last Spanish screens

- Status: **planned, plan reviews approved; not started** (2026-10-01). Planned from the hand-off at the end of `waves/P3/wave.md`.
- Goal (user outcome): a shop's profit screen keeps the sale of an order whose shirt had to be re-pressed (today it shows $0 revenue and a false loss); the Spanish floor header, QC result, busy panel and the designs catalog read cleanly at tablet and desktop sizes.
- Scope refs: always-in-scope (bug) for all cards: T-P4-1 (B-242, High: wrong profit), T-P4-2 (B-241 + es check), T-P4-3 (es check of /catalog/designs, B-184 confirm). Slot 4 (optional) is PM-ranked from the agent-doable Medium items.
- Fences: no deploys, no AWS, no outbound sends. Track D out. OI-17 and OI-18 are not approved. `invai-infra` is read-only and never pushed (OI-22). Waves 24 and 25 stay paused (decision 0019). No buyer PII. No rate limit or security control changed.
- Starts after: the P3 close-out gate and push (T-P3-3 invai-ui, T-P3-5 if it lands), so no unreviewed commit stacks on gated ones (lesson 2026-09-30 W23).
- Plan review: product-manager (scope + slot 4 ranking), architect (design of T-P4-1: reprint semantics across production and finance).

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| [T-P4-1](T-P4-1-reprint-revenue.md) Reprinted unit stays a sale: profit revenue, no re-import double unit (B-242) | backend-engineer (finance, orders, analytics, market) | opus | reviewer (fable) + architect (opus) | money, floor-correctness | planned |
| [T-P4-2](T-P4-2-floor-es-pass.md) Floor es: header pill fits (B-241); QC result and busy panel checked | floor-engineer | sonnet | reviewer (opus) + product-designer (sonnet) | ui | planned |
| [T-P4-3](T-P4-3-web-designs-es.md) Web es: /catalog/designs checked and fixed; billing numbers confirmed (B-184) | web-engineer | sonnet | reviewer (opus) + product-designer (sonnet) | ui | planned |
| [T-P4-4](T-P4-4-ai-reprint-units.md) Assistant/analyst queries count reprinted units (B-242 AI half) | ai-engineer | sonnet | reviewer (opus) | money | planned |
| [T-P4-5](T-P4-5-qa-reprint-fixtures.md) Acceptance fixtures use the real reprint model; market acceptance cache leak (B-221 rest) | qa-engineer | sonnet | reviewer (opus) | none | planned (after T-P4-1 commits) |

Interfaces: decision 0020 (`isReprint` = re-pressed, informational; a sale unit is any non-cancelled item) binds T-P4-1, T-P4-4 and T-P4-5; no shared file between cards; no contract change. Order: T-P4-1, T-P4-4, T-P4-2/3 in parallel (max 3 agents); T-P4-5 after T-P4-1 commits; one gate when all five are approved.

## Slots and ports
- T-P4-1: API :3140, Valkey DB 13. T-P4-2: API :3141, floor dev :5185, Valkey DB 14. T-P4-3: API :3142, web `pnpm build && pnpm preview --port 5186` with `VITE_API_URL=http://localhost:3142` (dev CSP is fixed to :3000, B-212), Valkey DB 12.
- Gate slot (:3000, :5173, :5174, :8000) stays free for `pnpm gate`.
- At most 3 agents at once, reviewers included, and at most 2 heavy test runs (full suite, gate, E2E) at once: on 2026-10-01 the machine hit about 15 of 16 GB with swapping and two full runs died.

## Integration gate
- [ ] `pnpm gate invai-ui invai-backend invai-imaging invai-floor invai-web` on a fresh seed
- [ ] Tech lead looks at: Profit losing orders (no Units 0 / $0 rows from reprints), floor header + QC result + busy panel in es at 1280×800, /catalog/designs in es at 1440 and 390
- [ ] Push backend, floor, web, docs (bare `git -C <repo> push origin main`); never invai-infra

## Build log
- 2026-10-01 Architect plan review: approve-with-changes (`reviews/plan-architect.md`, decision 0020): re-import double-creates a unit after a reprint today (never-double-ship bug), fix widens to orders/analytics/market/refunds; production unchanged; no migration or seed card. Cards T-P4-1 rewritten, T-P4-4 (ai) and T-P4-5 (QA fixtures + B-221 rest) added. PM scope review next.
- 2026-10-01 PM plan review: approve (`reviews/plan-pm.md`); B-243 waits for P5 (seed against T-P4-1's model). P5 candidates: B-243, B-224+B-238, B-233 rest. PM notes several backlog rows still say open though done (B-25, B-30, B-139, B-164, B-223); reconcile in P4 (haiku, backlog only).
- 2026-10-01 Plan and cards T-P4-1..3 written. B-242 filed from T-P3-4's finding. B-222 is already done (T-P1-5); B-184 looks done (no bare `toLocaleString` in billing), confirmed on T-P4-3.
