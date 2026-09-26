# Review of T-8-5 (round 1)

- Reviewer: qa-engineer on Sonnet 5
- Author: ai-engineer on Sonnet 5 (commit co-author line)
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend worktree add ../invai-backend-t85-review d3bbc80`, symlink `node_modules`, copy `.env` (blank `ANTHROPIC_API_KEY`) | isolated worktree at the reviewed commit only |
| `node_modules/.bin/tsx evals/run.ts` (= `pnpm evals`) | `mode: mock (no ANTHROPIC_API_KEY)`; 51/51 plumbing across listing_copy (21), trademark_judge (14), assistant (16); personalization_check correctly reported `skipped`; **exit 0** |
| `node_modules/.bin/tsx evals/run.ts nonexistent_route` | clean error, listed known routes, **exit 1**, process exits promptly (no hang) |
| Read all four `evals/*/cases.jsonl` in full | every case is invented shop/product copy, trademark strings or assistant questions; no real buyer/order/PII data anywhere; the `t82_injection_set`-tagged cases in `listing_copy` and `assistant` are a verbatim, correctly-attributed reuse of T-8-2's 7-string injection set, not new unvetted strings |
| Read `evals/lib/fixtures.ts` | eval tenant built from the same `src/test/fixtures.ts` (`createCompany`/`createUser`/`createLocation`) unit tests already use — no second, divergent way of making test data |
| `docker exec local-postgres-1 psql -U invai -d invai -c "select count(*) from companies where name like 'Eval harness%';"` | 13 rows present before cleanup — see finding below |
| `docker exec local-postgres-1 psql ... delete from companies where id in (<the 2 companyIds my own runs created>)` | `DELETE 2`; left everyone else's rows alone |
| `git worktree remove ../invai-backend-t85-review --force` | removed; no stray processes started (the harness is a one-shot script, not a server) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Harness + ≥10 PII-free cases per route | Yes | counts above; all four case files read in full, confirmed invented |
| 2. Scoring + per-route pass rate/cost/latency printed | Yes | `evals/lib/report.ts` output shown above has pass rate, cost median/p95, latency median/p95, cache-hit% per route, and a by-tag breakdown |
| 3. Mock mode auto, plumbing-only, no key | Yes | reproduced locally with a blank key; same is guaranteed in CI (no `ANTHROPIC_API_KEY` in `ci.yml`'s job env) |
| 4. `pnpm evals` documented + wired in CI + baseline checked in | Yes | `package.json`, `ci.yml` (right after `test`), `README.md`, `evals/baseline.json` all present and consistent with each other |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed — confirmed via reviewer's `git diff --stat`; no `e2e/**`, no acceptance-test files, nothing under QA's own owned paths touched.
- [x] Nothing outside scope.
- [x] Tests exercise the behavior, none weakened — this card adds a new harness, it doesn't touch any existing suite; `scan-test-weakening.sh` (run by the primary reviewer) found no hits inside `evals/**` or this card's other files beyond the intended `ci.yml` addition. The injection cases are a faithful reuse of T-8-2's set (same 7 strings, same tags), not a diluted copy.
- [x] Tenancy/idempotency/money/en-es — every DB call in the harness runs through `withTenant`/`withSystem` via the shared fixtures; no new tables or migrations; `costCents` pulled straight from `ai_jobs` as integer cents; idempotency N/A (no job/webhook, just read/insert eval calls); en/es N/A (dev console output).
- [x] Decisions recorded where needed — N/A, cites existing decision 0007.

## QA-specific notes
- **Golden path unaffected.** This card touches no `src/**`, no `e2e/**`, no fixtures QA owns (`src/test/**` is read-only-used, not modified). No re-run of `api-golden-path.spec.ts` was needed for this card.
- **Deterministic design is sound.** The assistant route's cases are checkable in mock mode because the mock still runs the real, company-scoped tools against a genuinely empty tenant (`deterministic: true` gates on a true fact — "0 orders", not a canned string). `listing_copy`/`trademark_judge` correctly mark quality as informational-only in mock mode, since `providers/mock.ts` is a fixed template/heuristic, not the model under test — scoring "quality" against it there would be a QA anti-pattern (asserting against your own stub). This matches the flaky-test / meaningful-assertion standard I hold E2E suites to.
- **Throwaway tenant hygiene (not blocking, but flagging as QA).** Confirmed live: running the harness leaves a permanent `companies` row (`Eval harness <timestamp>`) in whichever DB `DATABASE_URL` points at, with no delete path — 13 such rows already existed in the shared local dev DB before I even ran it. The report discloses this candidly as a known gap, and it's genuinely harmless (RLS-isolated, empty, no PII, and CI's Postgres container is thrown away at job end) — but it's exactly the kind of unbounded per-run data growth I'd flag in an E2E suite audit. Recommend a fast follow-up (delete-on-exit or a periodic sweep) before this runs on every CI push for weeks. I cleaned up the 2 rows my own review run created and left the rest for their original authors/the tech lead to deal with.
- **Injection case provenance verified.** Compared `t82_injection_set`-tagged cases against `src/ai/ai.test.ts`'s `INJECTIONS` array by reading both — all 7 strings match, including the one T-8-5 had to soften (dropping the raw NUL half of string #7) for the documented, separately-tracked NUL-byte bug (T-8-2, already fixed on top of this commit at `e0937cd`). Not a weakened test: the full string is still exercised at the source (`ai.test.ts`); this eval set just can't hit the crashing half until that fix lands, which the report states plainly.
