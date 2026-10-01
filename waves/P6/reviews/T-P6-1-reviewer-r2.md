# Review of T-P6-1 (round 2)

- Reviewer: reviewer on Opus 5.5
- Author: backend-foundation on Sonnet 5
- Verdict: approve

## Evidence I re-ran (invai-backend, commit a64533e)
| Command | Result |
|---|---|
| `pnpm typecheck` / `pnpm lint` | pass / 464 files, no fixes |
| `pnpm vitest run src/db/reset.test.ts src/db/seed --reporter=dot` | 7 files, 25 passed |
| a64533e's `safe-seed.test.ts` in a /tmp archive of fb424fe (round-1 guard) | 4 failed, 4 passed: both mixed cases red (DATABASE_URL scratch + MIGRATION invai; and the reverse). The archive was removed afterwards |
| `scan-test-weakening.sh invai-backend a64533e~1` | 4 removed asserts are the 2-arg calls, re-added with 3 args (lines 23-49); +2 mixed refusals, +1 mixed allow; no skips/mocks/config |
| `grep assertSafeToSeed(` | one caller, `seed/index.ts:95`, passes `env.DATABASE_URL, env.MIGRATION_DATABASE_URL, SEED_OUTPUT_FILE` |
| `grep settleQa src/db/seed/index.ts` | line 191 present (T-P6-4's 8de1b64). a64533e only touches the guard hunks |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1-4, 6 | yes | unchanged since r1 (evidence in r1). The guard tests are still green |
| 5 | yes | `seed/index.ts:69-86` refuses unless both URLs name `invai` or SEED_OUTPUT_FILE is set. Mixed-env tests are red on the old guard and green now. The reset half was met in r1 |

## Blocking findings
none (r1 finding 1 resolved)

## Checks
- [x] Only owned paths: `src/db/seed/index.ts`, `src/db/seed/safe-seed.test.ts`
- [x] No weakened tests; tenancy/idempotency/money/i18n n/a (dev tooling)
- [x] Shared `invai` DB and `seed-output.json` not touched; no processes left running

## Optional notes (not blocking)
- The r1 note still stands: importing the seed module registers market schedulers in Redis before the guard runs.
