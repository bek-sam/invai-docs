# T-P5-4: Backend fills alert params and timeline reason codes (B-224, B-238)

| Field | Value |
|---|---|
| Wave | P5 |
| Scope ref | `always-in-scope: bug` (Spanish leak on Today and the order timeline) |
| Spec | backlog B-224, B-238; the contract from T-P5-3 and its rulings in `reviews/plan-architect.md` |
| Owner | backend-engineer (area: today; orders timeline; alert callers in shipping, inventory, channels, vendors) |
| Reviewer | reviewer (opus) |
| Co-reviewers | architect (sonnet): contract consumer across modules |
| Risk flags | none |
| Model | sonnet |
| Depends on | T-P5-3 committed in invai-contracts |

## Owned paths (edit)
- `invai-backend/src/modules/today/**`
- `invai-backend/src/modules/orders/service.ts` and a new `orders/timeline.test.ts` (or the existing timeline test file in `modules/orders`, if it isn't `mapping.test.ts`)
- the `raiseAlert(` call sites in `invai-backend/src/modules/shipping/jobs.ts`, `inventory/jobs.ts`, `channels/jobs.ts`, `vendors/delivery.ts` (only the alert input objects)

## Read-only paths
- `invai-contracts/**`, `orders/mapping.ts` and `modules/catalog/**` (T-P5-2), `src/db/**`, `src/worker/**`, `src/ai/**`, `src/lib/**`, `src/test/**`

## Acceptance criteria
1. Every alert raised in the owned files fills the contract's `params` with the values its line needs (keys exactly as ruled); the alert row keeps them (the `alerts.data` jsonb, no migration) and `today` list procedures return them. `title`/`message` stay as the English fallback. Dates go out as ISO strings, never pre-formatted.
2. The order timeline returns `reasonCode` and `reasonParams` for every stored transition reason in the ruled enum, derived at read time in `orders/service.ts` from the stored reason (no producer change, no migration). Example: `reprint: misprint` → code for reprint + the reprint reason; `on sheet S-12` → sheet code + sheet name; an unknown string → no code.
3. Tests: one per alert kind you changed (params present, keys match the ruling) and a table test of reason string → code/params, including unknown and null. The old `message` text is unchanged (assert one).
4. Idempotency unchanged: re-raising an alert with the same `dedupeKey` updates params, doesn't duplicate.

## Verification
- `pnpm typecheck && pnpm lint 2>&1 | tail -n 20`; `pnpm vitest run src/modules/today src/modules/orders --reporter=dot 2>&1 | tail -n 20` in invai-backend. The gate runs the full suite.
- Exercise for real: API `PORT=3151`, Valkey DB 12. As `office@desertbloom.test`, call the Today alerts list and one order's timeline (an order with a reprint or a sheet step); paste one alert and one timeline entry (trimmed). As `presser@` the office procedure is refused.

## Out of scope
- Web (T-P5-5), alerts raised in `src/worker/**` or `src/ai/**`, changing what is stored on transitions.

## Rules
- Role file `.claude/agents/backend-engineer.md`. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/backend-engineer/`.
- Commit only your paths, attribution line at the end. **Don't push; only the tech lead pushes after the gate.** Foreground test runs only; record every PID you start and list it (stopped) in the report.
- Trim output. Report (≤ 60 lines) to `invai-docs/waves/P5/reports/T-P5-4.md`, one line per milestone as you go.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
