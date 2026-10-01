# T-P6-4: Seed counts repeat run to run (B-249); the stack is settled before the gate builds sheets (B-208)

| Field | Value |
|---|---|
| Wave | P6 |
| Scope ref | `always-in-scope: bug` (demo data shapes the product's numbers, CLAUDE.md seed-realism lesson; a sub-80% golden-path sheet makes the gate flaky on the wedge) |
| Spec | backlog B-249 (`waves/P5/reports/T-P5-1.md`, `reviews/T-P5-1-reviewer-r1.md`: shipped 628/638/638 on three runs; reprint pick `GROUP BY` + `LIMIT` with no order), B-208 (`waves/23/reviews/T-23-7-reviewer-r2.md` N5: 0.7951 film use when `production.batches.build` ran while the worker drained the post-seed outbox release, `src/db/seed/outbox-hold.ts`) |
| Owner | backend-foundation (seed) |
| Reviewer | reviewer (opus) |
| Co-reviewers | none (no schema, no product code); the architect's plan review rules on where the B-208 fix lives |
| Risk flags | floor-correctness (golden path step 5 sheet) |
| Model | opus |
| Depends on | T-P6-1 committed (it edits `src/db/seed/index.ts`; start from its commit) |

## Owned paths (edit)
- `invai-backend/src/db/seed/**`

## Read-only paths
- everything else: `src/modules/production/**` (batch build), `src/worker/**`, `src/lib/outbox.ts`, `src/db/reset.ts`, `src/api/**` (T-P6-2), `invai-web/e2e/**` (QA), `invai-infra/**`. If the right B-208 fix is outside the seed (for example in batch build or the gate script), stop that part, write the root cause and the exact suggested change with file:line in the report, and finish B-249.

## Acceptance criteria
1. B-249 root cause written in the report with file:line (every source of run-to-run variation: unordered `LIMIT`, random UUID order, `Math.random`, wall-clock dependence, worker timing).
2. Two full seeds on two fresh scratch DBs give identical counts on one SQL script (orders by state, items by state including shipped, reprints, sheets, shipments, labels, profit rows; ≤ 25 lines each, paste both). Which items get reprinted is the same set by order number and line on both runs.
3. Golden-path inputs do not move versus a seed of 471355a beyond what AC2's fix itself changes; if a count the E2E suites read changes, list it and why (the gate decides).
4. B-208: the report proves the race (which outbox events, still undrained when the gate builds the batch, change the item pool) and the fix makes the seed hand over a settled state: when `pnpm db:seed` exits, a `production.batches.build` on its data sees the same item pool whether or not the worker has drained yet (for example: the seed's own releases are applied before exit, or the events that change the pool aren't left for the worker). Show it: build counts/film use right after the seed with the worker stopped vs after the drain, same numbers. Every golden-path sheet ≥ 80% film use.
5. The seed's run time does not grow by more than 10%; it still finishes when imaging is unreachable as today; T-P6-1's output-file guard stays.
6. Architect ruling R2 (`reviews/plan-architect.md`): the fix lives in the seed. Likely mechanism, to confirm by measurement: the seed sets `qaStatus` "passed" without running QA (`builder.ts:548`); the released `design.updated` events make the worker run real QA, and a "failed" result drops items from the pool (`modules/production/sheets.ts:173`); pending personalized artwork becomes eligible only after the worker renders it (`sheets.ts:169`). Suggested fix: run `runDesignQa` and `renderPendingItem` inline before `releaseOutbox` (`builder.ts:2318`) and keep the release. If measurement shows another cause, follow the evidence and say so.
7. Seed tests (`src/db/seed/*.test.ts`) pass; add a test for any pure helper you introduce.

## Verification
- Scratch DBs `invai_p6_seed_a` and `invai_p6_seed_b`, imaging on :8031, `REDIS_URL=redis://localhost:6379/12` and `SEED_OUTPUT_FILE=/tmp/p6-4-seed-output.json` pinned **before** any reset, migrate or seed; a worker for the drain check uses the same env. Never reset or seed the shared `invai` DB. Drop both DBs at the end. Seeds are heavy: run them one at a time.
- `pnpm typecheck && pnpm lint 2>&1 | tail -n 20` and `pnpm vitest run src/db/seed --reporter=dot 2>&1 | tail -n 20` in `invai-backend` (explicit 600000 ms timeout on seed runs). Full suite and E2E at the gate.

## Out of scope
- B-130 (longer history), B-198, B-204, product code, schema, gate script, any change to which reprints exist (decision 0020; T-P5-1's 2–4% mix stays).

## Rules
- Role file `.claude/agents/backend-foundation.md`. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/backend-foundation/`.
- Other agents at the same time: backend-foundation on T-P6-2 (`src/api/events.ts`), floor-engineer on T-P6-3, reviewers. Don't touch their files.
- Commit only your paths, attribution line at the end. **Don't push; only the tech lead pushes after the gate.** Foreground test runs only; don't end your turn with a run or a process going. Record every PID you start (imaging, worker) and list it (stopped) in the report.
- Trim output (`2>&1 | tail -n 40`). Report (≤ 60 lines) to `invai-docs/waves/P6/reports/T-P6-4.md`, one line per milestone as you go.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
