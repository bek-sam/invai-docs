# Review of T-23-9 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: qa-engineer on Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web show --stat eb1e86b`; `git status --short` | 1 file, `e2e/digest-dates.spec.ts` +8/-1; tree clean |
| `pnpm typecheck` (invai-web, Node v24.21.0) | exit 0 |
| `pnpm lint 2>&1 \| tail -n 20` | exit 0, 1 pre-existing warning `src/content/markdown.test.ts:106` (not in diff) |
| `scan-test-weakening.sh invai-web eb1e86b~1` | removed=0 added=1, "Result: no hits" |
| Read `market/service.ts:432-438`, `tenancy/demo-flag.ts:6-30`, `market/jobs.ts:97,535-586`, `market/compute.ts:206-263,376`, `market/config.ts:110-116`, `ai/assistant-tools.ts:767` | see AC2 |
| E2E, DB | not run (decision 0019: gate runs them) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `digest-dates.spec.ts:57` auto-waits `toHaveText(ES_WEEKDAY_OR_MONTH)` on the one `h1`, then `:60-61` keep both original asserts unchanged. "Resúmenes" can't match the ES regex (`\b` breaks at `ú`), so the wait only passes once the detail heading is there. No `waitForTimeout`, retry or skip. The `{ timeout: 15_000 }` equals the config's `expect.timeout` (`playwright.config.ts:15`), so nothing is loosened. |
| 2 | yes (b) | Own source `mock` = `isSampleWorkspace` (`service.ts:437`). Desert Bloom isn't a sample workspace (`demo-flag.ts:12-22`). Outside mock rows come only from `market_series_cache` (`compute.ts:206-263`), and locally `mockSourcesAllowed` is true (`config.ts:114`). Only `refreshDemand` writes that cache (`jobs.ts:97`), and the seed never calls it (no hit under `src/db/seed`). The precondition is exact: at least one `market_series_cache` row with `mock=true` for the canonical queries (a global table) before the market suite runs. |
| 3 | yes | 0 removed `expect`s. One stricter `expect` added. No `.skip` or `fixme` (scan). |
| 4 | yes (per card's 2b branch) | Author: digest-dates 7/7 three times, and market blocked at `:101` as predicted. Not re-run by me; the gate runs it. |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`e2e/**` only)
- [x] Nothing outside scope (no product, seed or config edits)
- [x] Tests exercise the behavior; none weakened (scan clean, assertions kept)
- [x] Tenancy/idempotency/money/i18n: n/a (spec-only diff)
- [x] Decisions recorded where needed: none needed; follow-ups below

## Optional notes (not blocking)
- The AC2 wording "neither has fired" is too strong. `scheduleMarketJobs` (`jobs.ts:575`) uses BullMQ `every`, which runs its first tick immediately once a worker is up. But `marketSweep` enqueues `refreshDemand` only for shops with no `lead_time` signal today (`jobs.ts:549-558`). On a fresh seed, `design.updated` → `computeSignalsJob` (`jobs.ts:515`) has usually written that signal already, so the sweep skips the demand refresh. The precondition for T-23-10 is the same either way. Tell backend-foundation about this skip path.
- Follow-up (backend-foundation, not this card): `db:reset` obliterates BullMQ queues on whatever `REDIS_URL` is set (`src/db/reset.ts:91`). By default that is the shared dev Redis DB 0, and the author's run wiped other agents' queued jobs. The script should require or derive a non-default Redis DB when the target isn't the dev DB.
- Follow-up (web-engineer, not this card): the dev CSP `connect-src` is fixed to `http://localhost:3000` (`invai-web/vite.config.ts:16,33`). Every scratch-port API (the card's `PORT=3139`) is CSP-blocked in the browser. It should come from `VITE_API_URL`, as the prod path does (`vite.config.ts:40-47`).
