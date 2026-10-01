# T-P3-5: Market tests stop leaking rows into the global series cache (B-221)

| Field | Value |
|---|---|
| Wave | P3 |
| Scope ref | `always-in-scope: bug` (test isolation; can fail the gate; PM rank 3) |
| Spec | backlog B-221 (T-23-10 report) |
| Owner | backend-engineer (market) |
| Reviewer | reviewer (sonnet) |
| Co-reviewers | none |
| Risk flags | none (test code) |
| Model | sonnet |
| Depends on | starts after the P1+P2+P3 push |

## Owned paths (edit)
- `invai-backend/src/modules/market/**/*.test.ts` and market test helpers in `src/modules/market/` (product code only if a `clearCache()`-style helper is missing; say so)

## Read-only paths
- `src/test/**` (fixtures: backend-foundation), every other module

## Acceptance criteria
1. Every market test file that writes `market_series_cache` (frozen dates) cleans up what it wrote in `afterAll`/`afterEach`, or scopes its rows so other files can't read them.
2. `pnpm test src/modules/market` passes 5 runs in a row (paste the 5 exit codes), and twice with two runs in parallel (per-run isolation from B-228 should hold; if a deadlock appears, report it with the error).
3. No assertion is weakened, skipped or retried (`scan-test-weakening` must stay clean).

## Verification
- `pnpm typecheck && pnpm lint && pnpm test 2>&1 | tail -n 40` in `invai-backend` once at the end.

## Rules
- Role file `.claude/agents/backend-engineer.md`; `team/agent-brief.md`. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/backend-engineer/`.
- Commit only your paths, attribution line at the end. **Don't push; only the tech lead pushes after the gate.** Record PIDs of anything you start; drop any DB you pin.
- Report (≤ 60 lines) to `invai-docs/waves/P3/reports/T-P3-5.md`.
