# Review of T-P6-2 (round 1)

- Reviewer: reviewer on sonnet
- Author: backend-foundation on opus; commit invai-backend `5557014`
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck` | clean |
| `pnpm lint` | 462 files, no fixes |
| `pnpm vitest run src/api/events.test.ts --reporter=dot` | 1 file, 11 passed, 4.25s (Vite-exit warning pre-existing, also seen alone on `src/auth.test.ts`) |
| `git worktree add --detach /tmp/review-tp62-base 471355a`; copy `events.test.ts` as-is | `TypeError: createEvents is not a function`, 0 tests run (matches author's claim) |
| Same worktree, hand-added a minimal `createEvents({ pingMs })` shim with **no** recheck/probe logic (base behavior otherwise unchanged); ran the test file | 8 failed / 3 passed — exactly the 3 preserved behaviors (Bearer→200, still-valid keeps pinging, shutdown-unchanged); the ?token= tests and all 5 revoke tests fail on base, proving the new tests discriminate the real behavior change, not just the new export |
| `git worktree add --detach /tmp/review-tp62-head 5557014`; mutated `recheck()`'s `return (await probe()) ? "revoked" : "unknown"` to `return "revoked"` (drop ruling C1's DB-down guard); ran the test file | exactly 1 failure: "database unreachable on re-check: retry hint, never unauthorized (ruling C1)" — 10/11 still pass, confirming that test is the sole guard against a DB blip looking like a revoke |
| `pnpm test` (full suite) first run | 1 file / 2 tests failed (unrelated to events.test.ts, which was all-green in that same run); re-ran full suite once more | 180 passed / 2 skipped, 1475 passed / 3 skipped / 1 todo — all green; first run's 2 failures were transient (shared-infra contention), not reproduced |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend origin/main` | no hits in tracked diff (one untracked `src/db/seed/plan-order.test.ts` from a concurrent agent's WIP, unrelated) |
| `git show 5557014 --stat`; `git diff 471355a 5557014 --stat -- context.ts realtime.ts shutdown.ts tenancy/` | commit touches only `src/api/events.ts` + `src/api/events.test.ts`; all read-only paths unchanged |
| `grep -n "events" src/api/app.ts` | still mounts `events` (now `createEvents()`'s default instance) at `REALTIME_SSE_PATH` |
| `grep -rn "unauthorized" invai-contracts/src/realtime.ts` | not present — no contract change, as required |
| Live: `PORT=3153 REDIS_URL=redis://localhost:6379/9 pnpm dev:api`, signed in as `owner@desertbloom.test` | cookie stream → `ready`+`ping`; `?token=<session>` → `401 {"error":"unauthorized"}`; sign-out at 09:50:13 → `event: unauthorized` observed by 09:50:30 (within one 25s ping), 0 lines matching `^retry:`; reconnect with the same cookie → 401 |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `?token=` ignored on route and mounted app (tests + live curl 401); Bearer/cookie 200 (tests + live); `lastEventId`/`Last-Event-ID` code path untouched (diff) |
| 2 | yes | revoked station token, `revokeFloorSession`, deactivated member tests all end with `event: unauthorized` + stream close + 401 reconnect; mutation test confirms the C1 guard is load-bearing |
| 3 | yes | web sign-out test + my own live cookie sign-out probe, closed within one ping interval |
| 4 | yes | recheck reuses `buildContext(authRequest())` on the original headers (diff `events.ts:63-72`); company-mismatch test; C1 `select 1` probe gates `unauthorized` vs `shutdown`+`retry:5000`; `unauthorized` has no `retry:` (test + live grep) |
| 5 | yes | shutdown test unchanged (`retry: 1000`, real 25s interval, wakes on signal not timer) |
| 6 | yes, independently reproduced | base-archive crash (0 tests) and shim-added 8-fail/3-pass both confirmed myself, not just taken on the author's word |
| 7 | yes | read `invai-web/src/lib/realtime.ts:120-152`: native `EventSource`, no `unauthorized` listener; per spec a non-200 response on reconnect sets `readyState` to `CLOSED` permanently (no retry loop) — matches the author's claim |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`git diff --stat` on `5557014`: `src/api/events.ts`, `src/api/events.test.ts` only)
- [x] Nothing outside scope (`context.ts`, `realtime.ts`, `shutdown.ts`, `tenancy/floor-auth*` byte-identical to base; no contract change)
- [x] Tests exercise the behavior, none weakened (`scan-test-weakening.sh` clean; mutation-tested both the base-vs-head gap and the C1 guard)
- [x] Tenancy: company + sessionKind compared every recheck, no new `withSystem`, no PII in new log lines (ids only)
- [x] Idempotency/jobs: n/a (no job/webhook/payment touched)
- [x] en/es, money, sizes: n/a (no user-facing copy or data shape changed)
- [x] Decisions recorded where needed: C1/C2 already recorded in `plan-architect.md`; no new decision needed

## Optional notes (not blocking)
1. Agrees with the security co-reviewer's note #1 (`T-P6-2-security-reviewer-r1.md`): a transient `buildContext` pool-timeout error followed by a succeeding `select 1` probe reads as a revoke for that one stream (tablet relocks, recovers by PIN). Fenced by `context.ts` read-only; Low, backlog candidate.
2. The full-suite's one transient 2-test failure on the first run (not reproduced on immediate re-run, and `events.test.ts` itself was green both times) is consistent with shared dev-infra contention from other agents' concurrent runs, not this diff — noting it here only so the tech lead isn't surprised if seen again.
