# T-P7-1: The golden-path suites hold the mock Shopify auto-import while they run (B-255)

| Field | Value |
|---|---|
| Wave | P7 |
| Scope ref | `always-in-scope: bug` (B-255: the worker's 10-minute mock Shopify poll imports 1-3 orders during the gate, so the step 5 sheet pool grows 39→42 between seed and build; flaky gate on the wedge) |
| Spec | backlog B-255; `waves/P6/reports/T-P6-4.md` (finding 2); `waves/P6/reviews/T-P6-4-reviewer-r1.md` |
| Owner | qa-engineer |
| Reviewer | reviewer (opus) |
| Co-reviewers | none |
| Risk flags | golden path |
| Model | sonnet |
| Depends on | plan review (architect ruling on the mechanism; default below) |

## Owned paths (edit)
- `invai-web/e2e/api-golden-path.spec.ts`, `invai-web/e2e/golden-path.spec.ts`, `invai-web/e2e/helpers/**`

## Read-only paths
- Everything else, including `invai-backend/**` (`modules/channels/sync.ts:627-668` `pollableConnections`, `jobs.ts` poll schedule, `integrations/channels/shopify/mock.ts`), `invai-contracts/**`, `invai-infra/**` (gate.sh is read-only: OI-22). If the fix needs a product change, stop and report.

## Mechanism (default; the architect's plan review may replace it before you start)
The poll already skips a connection whose `settings.autoImport` is `false` (`sync.ts:658`), and owners can set it through `channels.update` (`ConnectionSettings.autoImport`). The suites turn auto-import off on every API connection of Desert Bloom at their start (as `owner@`), and turn back on exactly the ones they turned off at their end (also when a test fails: `afterAll`), so the dev DB the gate leaves behind still shows imports landing.

## Acceptance criteria
1. Given a fresh seed and a running worker, when the API golden-path suite runs, then no channel poll imports orders between its first and last test: the step 5 preview and the build see the same pool whatever the wall-clock minute. Log the pool size (preview item count) at step 5 in both suites.
2. After either suite ends (pass or fail), every connection's `autoImport` is what it was before the suite (prove with a forced failure once, then revert it).
3. The suites still pass their 13 steps unchanged in meaning: no assertion loosened, no retry or sleep added, the ≥ 80% film-use check on full sheets kept.
4. The residual window (a poll that fires between the stack restart and the suite's first test) is measured or argued in the report, with the number of orders it could add (the mock adds 1-3 per tick, deterministic by cursor).
5. Proof the hold works: on your scratch stack with the worker running, with auto-import off across one poll tick (the tick is on the 10-minute wall-clock boundary plus a fixed per-connection jitter, `jobs.ts:36-50`), no new mock order (`#3xxx`) arrives; with it on, the next tick imports. Give the times and counts.

## Verification
- Scratch stack: create `invai_p7_gp` (owner `invai`), `MIGRATION_DATABASE_URL`/`DATABASE_URL` pointing at it, `REDIS_URL=redis://localhost:6379/12`, `SEED_OUTPUT_FILE=/tmp/p7-1-seed-output.json`, imaging on :8071, then `pnpm db:migrate && pnpm db:seed` in `invai-backend`; API `PORT=3171`, worker with the same env.
- `cd invai-web && E2E_API=1 E2E_API_URL=http://localhost:3171 pnpm e2e e2e/api-golden-path.spec.ts --reporter=line 2>&1 | tail -n 30` (explicit 600000 ms timeout), twice on two fresh seeds if time allows.
- `pnpm typecheck && pnpm lint 2>&1 | tail -n 20` in `invai-web`. The browser suite runs at the gate (it needs :3000 / :5173).

## Out of scope
- Backend, contract or infra changes; the seed; nesting quality; the screens smoke spec.

## Rules
- Role file `.claude/agents/qa-engineer.md`. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/qa-engineer/`.
- Other agents at the same time: platform-sre (`.claude/hooks/**`), product-designer (`invai-ui`), ai-engineer (`invai-backend/src/ai/**`). Don't touch their files; don't use :3000, :5173, :5174, :8000.
- Commit only your paths, attribution line at the end. **Don't push; only the tech lead pushes after the gate.** Foreground test runs only (explicit 600000 ms timeout on suites); don't end your turn with a run or a process going. Stop your API, worker and imaging and drop `invai_p7_gp` before you hand back. Record every PID you start and list it (stopped) in the report.
- Trim output (`2>&1 | tail -n 40`). Report (≤ 60 lines) to `invai-docs/waves/P7/reports/T-P7-1.md`, one line per milestone as you go.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
