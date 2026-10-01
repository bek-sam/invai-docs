# Review of T-P1-3 (round 1)

- Reviewer: reviewer on Claude Opus 5.5
- Author: ai-engineer on Claude Opus 5.5 (report header; the card asked for sonnet)
- Verdict: changes-required

## Evidence I re-ran (invai-backend at b81a038; T-P1-4's uncommitted files ignored)
| Command | Result |
|---|---|
| `pnpm typecheck` / `biome check <13 changed files>` | clean / clean. Repo-wide `pnpm lint` fails only on an untracked `tmp-enqueue-previews.ts` that belongs to another agent |
| `pnpm test src/ai src/modules/ai src/modules/market src/db/rls-coverage.test.ts src/api/authz.test.ts --reporter=dot` | 21 files, 290 passed, 1 skipped |
| `publish.acceptance.test.ts` run 5 times | 3/3 passed in each of the 5 runs |
| `engine.test.ts` copied onto base 5649c7c | AC34 and the pinned Oct test fail (2 failed), so the new test proves the change |
| `pnpm evals <route>` for each route (mock) | listing_copy 21/21, trademark_judge 14/14, assistant 42/42 (quality 28/28), digest_narrative 22/22. Companies: 5 before, 6 after (see finding 2) |
| API on :3157 (PID 83752, stopped), curl `ai/assistant/ask` as owner, en, es and seasonality | 0 `**` and no `_` markup. es body ends "(Modo demo: …)". Raw SSE ends `event: done` / `data: {}` |
| scan-test-weakening.sh | Hits: publish `urls`→`keys` (AC7 as designed; the 4 other asserts are unchanged), engine Oct expectation re-pinned (the method changed; peak and off assertions kept), regexes and strings with `**` removed (they follow the text change) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 B-192 | **no** | The under-way branch works (new test, en and es). But a past act-by date still prints when the peak is near: see finding 1 |
| 2 B-135 | yes | Live curl in en and es: no markers, Spanish footer |
| 3 B-132 | backlog | The claim holds. `@orpc/shared` index.mjs:263-265 runs the cleanup when `next()` is done, and `@orpc/standard-server-fetch` index.mjs:65 calls `reader?.cancel()` there. The server always sends `event: done` with `data: {}`: the RPC serializer turns `ask()`'s undefined return into `{}`, so the client cancels before end-of-stream. Neither the backend generator nor `assistant.tsx:124` (a full for-await with no break) can avoid it. No fix exists inside the owned paths |
| 4 B-114 | yes | `service.test.ts` B-114 test passes |
| 5 B-165 | **no** | See finding 2 |
| 6 B-131 | yes, see finding 3 | Matches Step 3a steps 1–6 and the gate. AC34 test fails on the base code |
| 7 B-229 pt 2 | yes | Only the URL→key comparison changed |
| 8 | yes | Tests and mock evals pass; publish passed 5 runs in a row |

## Blocking findings
1. `src/modules/ai/assistant-tools.ts:1034`: only `weeksToPeak === 0` is handled. When 0 < weeksToPeak < leadTime, `actBy()` (signals.ts:307) returns a date that is already past. Probe: `actBy(2026-09-20, [10], 4, "America/Phoenix")` gives `{date:"2026-09-03", weeksToPeak:1.57}`. The tool then prints "Act by 2026-09-03: 2 weeks to the peak… Act now." on Sep 20, a common case for Halloween with a 4-week lead time. That fails AC1 ("never prints an act-by date in the past"). Fix: drop the date when it is before today, and add a test for this case.
2. `evals/assistant/seed.ts:38` (`createSeededEvalTenant`): the assistant route creates a second tenant, "Eval analyst <ts>", and nothing deletes it. `run.ts`'s `finally` removes only the tenant from `createEvalTenant`. I reproduced it on the dev DB: after `pnpm evals assistant` that company was still there. I deleted it myself afterwards; the count is back to 5. AC5 is not met for the route that is run most often.
3. `src/modules/market/signals.ts:230-244`: an all-zero series now returns a flat SI (all 1.0, `yearsUsed` 3) instead of `null`. The probe confirms it. The docstring still says `null` for this case. In `compute.ts:577-594`, an outside niche series that is all zero (for example a low-interest Trends niche) now stores a "seasonality" signal with no peaks. The source-priority fallback (own → outside → Census) then stops at it, and Census is never used for that niche. Fix: `if (sorted.every((p) => p.value === 0)) return null`, plus a test.

## Checks
- [x] Only owned paths changed: 13 files under `src/ai`, `src/modules/ai`, `evals`, plus the granted `market/signals.ts` and `engine.test.ts`
- [x] Nothing outside scope (no web, no prompt change)
- [x] Tests exercise the behavior; none weakened (scan hits explained above)
- [x] Tenancy: `withSystem` in `deleteEvalTenant` is eval-only cleanup with a reason comment; no request path or table changes. en/es: "La temporada ya está en curso." and "Modo demo" read fine
- [x] Decisions: none needed

## Optional notes (not blocking)
- Step 3a defines t as the chronological month index. The code uses the array index, so a month missing from `weeklyToMonthly` shifts t. Own series can have mid-series gaps.
- AC34(b) checks growth with `ols` directly, not through `fitTrend`'s `rising` class as spec AC34 states.
- Older analytics tools answer in English to Spanish questions (author's own note). That needs its own card.
