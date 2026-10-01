# T-P5-3: Contract: alert params and timeline reason codes, additive (B-224, B-238)

| Field | Value |
|---|---|
| Wave | P5 |
| Scope ref | `always-in-scope: bug` (Today alert lines and timeline reasons stay English under Spanish; the contract carries only English text) |
| Spec | backlog B-224, B-238; `invai-web/src/features/orders/timeline-reason.ts` (current parsing); `invai-backend/src/modules/today/service.ts` `generateAlerts`; `orders/service.ts:639` (timeline message) |
| Owner | architect |
| Reviewer | reviewer (sonnet) |
| Co-reviewers | none (the architect owns the contract; T-P5-4 and T-P5-5 consume it) |
| Risk flags | contract |
| Model | opus |
| Depends on | plan reviews |

## Owned paths (edit)
- `invai-contracts/src/**`, `invai-docs/decisions/` (one file + index row if you record a decision), `invai-docs/waves/P5/reviews/plan-architect.md`

## Read-only paths
- every other repo (grep consumers, don't edit them)

## Acceptance criteria
1. `Alert` gets an optional, typed way to carry the values a translated line needs (for example `params: Record<string, string | number>`), with a short doc comment listing the keys each alert kind uses today (order number, ship-by date as an ISO string, hours, SKU, sheet name, count…). Dates travel as ISO strings; the web formats them. `title` and `message` stay (English fallback, old clients).
2. `TimelineEntry` gets optional `reasonCode` (a closed enum of the reasons the backend writes today; read the producers: `orders/mapping.ts`, `orders/import.ts`, `orders/service.ts`, `production/floor.ts`, `production/sheets.ts`, `shipping/service.ts`) and optional `reasonParams` (for example the sheet name, the reprint reason). Unknown or free-text reasons map to no code; `message` stays.
3. Purely additive: no existing enum gets a value, no field becomes required, no field is removed (lesson 2026-10-01 A2: an enum addition breaks exhaustive switches in consumers). Show the grep across backend, web and floor that nothing breaks; `pnpm typecheck` passes in invai-backend, invai-web and invai-floor against your commit.
4. The exact field names, enum values and param keys are written in `reviews/plan-architect.md` (rulings) so T-P5-4 and T-P5-5 build against them.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test 2>&1 | tail -n 20` in `invai-contracts`; `pnpm typecheck 2>&1 | tail -n 5` in invai-backend, invai-web, invai-floor.

## Out of scope
- Backend and web changes (T-P5-4, T-P5-5). Alerts raised outside `src/modules/**` (worker sweeps, outbox relay, ai breaker) may stay title-only.

## Rules
- Role file `.claude/agents/architect.md`. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/architect/`.
- Commit only your paths, attribution line at the end. **Don't push; only the tech lead pushes after the gate.** Record every PID you start.
- Report (≤ 40 lines) to `invai-docs/waves/P5/reports/T-P5-3.md`.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work.
