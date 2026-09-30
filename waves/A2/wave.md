# Wave A2: analytics v2, screens, assistant and digest (B-173..B-177)

- Status: **not started.** Written by the A1 tech lead as a hand-off on 2026-09-30. A fresh tech lead plans this wave from here (CLAUDE.md token budget, decisions 0018 and 0019).
- Spec: `specs/business-analytics-v2.md` (status `ready`), tracks T-A6..T-A10. Scope check: `waves/analytics-scope-check.md`.

## Handoff from wave A1 (2026-09-30, tech lead)
- **State:** A1 is done and pushed after a full `pnpm gate` pass (`invai-infra/.gate/run-20260930T172303Z.log`): contracts `f466088` (contract 0.9.0, `analytics.*`), backend `5170e12`, web `369705f`, floor `72a842d`. All 5 cards are approved with evidence in `waves/A1/reviews/`. The dev DB is freshly seeded by that gate (5377 orders, 19 months of history, Q4 2025 peak about 2.1x, seed 43 s), plus 2 orders moved through press, QC and pack by the screen check.
- **The API is ready for screens:** `analytics.{unitEconomics, losingOrders, leakage, shippingMargin, profitBridge, breakEven, operations, inventoryHealth, supplierTrends, designLifecycle, export}`; `CostSettings.fixedMonthlyCents`; `Shipment.destZone`; v6 assistant tool names are reserved in the contract.
- **Candidates (PM ranks, at most 5):** B-173 Profit v2 screens, B-174 Operations and Inventory health screens plus the Designs lifecycle column, B-175 assistant tools v6 with evals (ai-engineer co-reviews), B-176 digest detectors D9..D13, B-177 Today actions panel (depends on B-176). Their backlog status still says "PM to confirm". The PM confirms scope and sets the order.
- **Sequence:** B-173 and B-174 both edit web, so give each an exact route and file set, and never both on `routes/_app/profit*`. B-176 must land before B-177. B-175 needs no web change.
- **Fold into cards (from A1):**
  - B-226 Profit es: the Costos KPI is clipped at 1440 px, and the chart axis and margin use English number formats. Goes into B-173.
  - A1 review notes: T-A3 channel and service groupings sort by margin only (add a tiebreak); `shipmentsWithoutZone` counts orders but the contract text says shipments (architect decides which to fix); `break_even.sql` v2 (Net includes dated refunds) for the data-analyst.
  - AC-C1's "G64000 Sand L under-stocked" premise came from the old seed. With the new seed, the top size gaps are BC3001 Black 3XL (+18.0 pts) and Dusty Blue L (−18.6 pts). Fix screen tests and help text to match.
- **Open small bugs from the A1 gate (always in scope, card them if a slot opens):** B-222 floor QC "APROBAR" banner in Spanish (Medium, floor-engineer), B-223 raw English timeline string, B-224 English Today alerts, B-225 Today date locale (a B-207 repeat; add a lint ban), B-227 `db:reset` deadlock flake in the gate.
- **Environment:**
  - Use `pnpm gate <repos>` with the repos named explicitly. Infra must stay out: it holds unpushed T-23-6, T-23-7 and T-24-1 commits, and OI-22 is unanswered.
  - If `db:reset` deadlocks (40P01), re-run the gate once (B-227).
  - Playwright output now goes to `../.e2e-out/<repo>/`.
  - An unknown API is listening on :3142 (PID 30429, parent 11838). Leave it alone.
  - `invai-docs/.claude/agent-memory/` is a stray, untracked folder created by agents started inside `invai-docs`. The product-manager and reviewer memory files there belong in `/Users/bekbolsun/invai/.claude/agent-memory/`. Its owners should move them. Don't commit it.
  - Disk: 14 GB free (OI-20).
- **Fences:** Track D (B-178..B-181) stays out. OI-17 and OI-18 are not approved. No buyer PII in analytics, screens or AI prompts.

## Cards
(to be written by the A2 tech lead)
