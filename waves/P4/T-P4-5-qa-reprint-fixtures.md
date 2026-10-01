# T-P4-5: Acceptance fixtures use the real reprint model; market acceptance files stop leaking cache rows (B-242, B-221 rest)

| Field | Value |
|---|---|
| Wave | P4 |
| Scope ref | `always-in-scope: bug` (fixtures model reprints as a sibling row that doesn't exist; market acceptance files leak into the global cache and fail ~2 of 5 runs) |
| Spec | `reviews/plan-architect.md` ruling 7; decision 0020; backlog B-221 (rest after T-P3-5 9eae8fd) |
| Owner | qa-engineer |
| Reviewer | reviewer (opus) |
| Co-reviewers | none |
| Risk flags | none (test code) |
| Model | sonnet |
| Depends on | T-P4-1 committed (the reprint fixtures must match its fix); the B-221 half can start at once |

## Owned paths (edit)
- `invai-backend/src/modules/market/market.acceptance.test.ts`, `market-prod-mode.acceptance.test.ts`, `market-outage.acceptance.test.ts`, `invai-backend/src/modules/digest/digest.acceptance.test.ts`

## Read-only paths
- product code, `market/service.test.ts` (T-P3-5), every file T-P4-1 owns, `src/test/**`

## Acceptance criteria
1. `market.acceptance.test.ts:666` and `digest.acceptance.test.ts:501` build a reprint as the same item re-pressed (second transfer, `isReprint` on that item), not a sibling revenue-0 row; assertions follow decision 0020 (the reprinted unit counts). The report lists every assertion value that changed and why; none is loosened (no wider ranges, no removed checks).
2. B-221 rest: every market acceptance file that writes `market_series_cache` clears it in `afterAll` (as 9eae8fd did in `service.test.ts`), and awaits any `refreshDemand` before teardown (the "pool after end" error in `market-prod-mode`).
3. `pnpm vitest run src/modules/market --reporter=dot` passes 5 runs in a row, run one after another in the foreground (paste the 5 exit codes). No parallel pair this time (RAM).
4. No skip, retry or timeout raise (`scan-test-weakening` clean).

## Verification
- `pnpm typecheck && pnpm lint 2>&1 | tail -n 10` in `invai-backend`; the market and digest acceptance files; the gate runs the full suite.

## Rules
- Role file `.claude/agents/qa-engineer.md`. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/qa-engineer/`.
- Commit only your paths, attribution line at the end. **Don't push; only the tech lead pushes after the gate.** Foreground test runs only; don't end your turn with a run going. Drop any test DB you pin.
- Report (≤ 50 lines) to `invai-docs/waves/P4/reports/T-P4-5.md`, one line per milestone.
