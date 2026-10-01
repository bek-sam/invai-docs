# Review of T-P1-3 (round 2)

- Reviewer: reviewer on Claude Opus 5.5. Author: ai-engineer on Claude Opus 5.5
- Diff: invai-backend `c9fa1e5` (5 files: `evals/assistant/run.ts`, `src/modules/ai/assistant-tools{,.test}.ts`, `src/modules/market/{signals.ts,engine.test.ts}`), all inside the r1 owned or granted paths
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck` / `pnpm lint` | exit 0 / 453 files, no issues |
| `pnpm test src/ai src/modules/ai src/modules/market --reporter=dot` | 19 files passed, 1 skipped; 278 passed, 1 skipped |
| tsx probe of `actBy(d, [10], 4, "America/Phoenix")` | 09-20: date 09-03, wtp 1.57, suppressed, date is past. 09-03: wtp 4, not suppressed, date = today. 09-04: wtp 3.86, suppressed, date is past. `weeksToPeak < leadTimeWeeks` is true exactly when the date is before today |
| tsx probe `seasonalityIndex(36 zero months)` | `null` |
| `pnpm evals assistant` (mock) | quality 28/28. Dev DB `companies` 5 before, 5 after, 0 named `Eval%` |
| Failure path: temp script (deleted) calling `runAssistantEvals` with a tenant that throws on access | rejected with "injected failure"; `companies` still 5, so the seeded tenant was deleted in `finally` |
| `scan-test-weakening.sh invai-backend c9fa1e5~1` | 0 assertions removed, 6 added. One hit: `getSeasonalitySignal.mockImplementation`, a dependency stub in the same style as the tests next to it, not the unit under test |

## Round 1 blocking findings
1. B-192 past act-by date: **fixed**. `assistant-tools.ts:1036` now checks `weeksToPeak < leadTimeWeeks`. The new test uses the exact Sep 20 probe values and checks en and es: the "season is on now" copy shows, and "2026-09-03" and "Act by" do not. On the base code this test fails, because the base printed "Act by 2026-09-03" when wtp was 1.57.
2. B-165 seeded tenant: **fixed**. `evals/assistant/run.ts:64-75` deletes it in `try/finally` and only logs if the delete fails. Both the success and failure runs above left the count at 5.
3. B-131 all-zero series: **fixed**. `signals.ts:237` returns `null` before the OLS step, so `compute.ts` falls through to Census again. The new `engine.test.ts` test passes, and AC34 (the Step 3a worked example) and the pinned October test still pass in the run above.

## Acceptance criteria
AC1, AC5 and AC6 now pass, with the evidence above. AC2, AC4, AC7 and AC8 passed in r1, and their code is unchanged. AC3 (B-132) is in the backlog, as recorded in r1.

## Checks
- [x] Owned paths only; nothing out of scope; no test weakened
- [x] Tenancy: no new `withSystem` (cleanup reuses `deleteEvalTenant`); no request-path or schema change
- [x] en and es both covered by the new test

## Optional notes (not blocking)
- If `createSeededEvalTenant` fails partway, it runs before the `try` and could leave a half-built tenant. This is rare and only affects evals.

## Processes and data
- No API started. Port :3142 is held by another agent (PID 91823); I left it alone. Dev DB left at `companies` = 5, with no reset.
