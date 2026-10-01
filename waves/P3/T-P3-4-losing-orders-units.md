# T-P3-4: Profit "Orders that lost money" shows Units 0 and Revenue $0 (B-230, verify first)

| Field | Value |
|---|---|
| Wave | P3 |
| Scope ref | `always-in-scope: bug` (profit numbers; PM rank 2) |
| Spec | backlog B-230; `waves/A2/wave.md` line 72 |
| Owner | backend-engineer (analytics/finance) |
| Reviewer | reviewer (opus) |
| Co-reviewers | none |
| Risk flags | none (read-only report query) |
| Model | sonnet |
| Depends on | starts after the P1+P2+P3 push |

## Owned paths (edit)
- `invai-backend/src/modules/analytics/finance-service.ts` (`losingOrders` only) and its tests

## Read-only paths
- every other module, `src/db/**`, `src/test/**`, `invai-web/**`, `invai-contracts/**`

## Acceptance criteria
0. **Verify first:** on the dev DB (read-only queries), for 3 seeded losing orders, report their items, reprint flags, cancel state, revenue lines and why units/revenue come out 0. State: query gap, or the orders really are reprint-only/cancelled.
1. If a query gap: units = physical units sold on the order (non-reprint items), revenue = the order's sale revenue as the profit screen's other tables compute it; a test with a fixture shop pins a losing order with 2 units and its revenue. CM2 and cost lines unchanged.
2. If the data is right: no product change; report why, and propose the copy or seed change (owner named) instead.
3. Tenant isolation: the query stays under `withTenant`; existing tenancy test still passes.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test 2>&1 | tail -n 40` in `invai-backend`.
- Exercised: own API `PORT=3138`, `REDIS_URL=redis://localhost:6379/13`, sign in as `owner@desertbloom.test`, call `analytics.losingOrders`; units and revenue in the report. Refused case: `presser@` → FORBIDDEN.

## Rules
- Role file `.claude/agents/backend-engineer.md`; `team/agent-brief.md`. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/backend-engineer/`.
- Commit only your paths, attribution line at the end. **Don't push; only the tech lead pushes after the gate.** Record PIDs, stop them, flush Valkey DB 13. Never reset the dev DB.
- Report (≤ 60 lines) to `invai-docs/waves/P3/reports/T-P3-4.md`.
