# Review of T-29-2 (round 1)

- Reviewer: reviewer on fable
- Author: backend-foundation on opus (backend `384ef6f`, docs `fd3caf7`)
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend show 384ef6f --stat`; `git status --short` | 9 files, all inside the card's owned paths or the author's role paths (context.ts, see notes); tree clean |
| `pnpm typecheck && pnpm lint` (in tree, HEAD 384ef6f) | tsc clean; biome 513 files, no issues |
| `pnpm exec biome check <9 changed files>` | 9 files, no issues |
| `pnpm vitest run --reporter=dot src/lib/account-lockout-notify.test.ts src/lib/account-security.test.ts src/lib/account-lockout src/modules/tenancy src/api/authz.test.ts src/db/rls-coverage.test.ts src/auth` | 14 files, 123 tests passed, exit 0 |
| `pnpm test -- --reporter=dot` (full suite, shared `src/lib`/`src/api` touched) | 1697 passed, 3 skipped, 1 todo, exit 0 (320 s) |
| Red on base: worktree at `95324fe` + the two test files from `384ef6f` | `account-security`: 2 fail (`sample: true` unit case `expected true to be false`; seeded `demo = true` case `expected false to be true`). `account-lockout-notify`: fails on the missing `errorKind` export; with that import dropped it fails at `lines.some("lock email failed")` (expected false to be true), the right reason. Worktree removed |
| `scan-test-weakening.sh invai-backend 2529441` | hits: `vi.mock("./account-lockout")` (a dependency of the hook under test, spread from the original, only `notifyLocked` replaced: OK); console spies restored in `finally`; 3 removed assertions re-stated as `sample:` cases plus an `it.each` of 3 (live, retired, seeded). No skip/only/snapshot/config hits |
| Live API `PORT=3123 REDIS_URL=redis://localhost:6379/11` (PID 45956, dev DB read-only, sign-ins only) | owner@ `mfa {required:true, enabled:false, deadline 2026-10-16T15:45:15.686Z}` (seed 15:45:15 + 7 d); admin@ same shape; office@ and vendor@ `required:false, deadline:null`; owner `orders.list` 200 in grace. API log: 0 lines with an email. Stopped, `lsof :3123` empty |
| `psql` dev DB read-only | Desert Bloom `demo=t, demo_owner_user_id=null, demoRetiredAt=null`; 0 sample rows; seeded 2026-10-09 15:45 so the live check is valid |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | Live owner@/admin@ required with +7 d deadline; orders.list 200 in grace. Past deadline: unit `it.each` seeded case `mfaBlocks` true at start+7 d, live/retired sample cases `required:false, deadline:null` (test, red on base). `isMfaRequired` signature unchanged; `MfaMembership.demo` -> `sample` via `isSampleRow` in the join |
| 2 | yes | Live vendor@ and office@ `required:false`; unit cases for vendor/office kept (`sample:` form) |
| 3 | yes | `auth.ts:396` `.catch` logs `errorKind` only (class + PG code, `account-lockout.ts:42`); test asserts 401 unchanged, `DrizzleQueryError`/`57P01` logged, email absent from every log line, process `unhandledRejection` spy not called, red on base. `server.ts:56` and `worker/index.ts:99` log-and-continue through `logger`; `grep uncaughtException src` = comments only, Node default kept |
| 4 | yes | ADR 0028 §3 states it; new reactivation test (restart once, no second restart) + `tenancy/security.test.ts` pass; no code change |
| 5 | yes | Fresh seed deadline is 7 d out; no E2E references the banner (not run here, gate). Report and 0028/0029 say reseed or enroll on a DB older than 7 d |

## Blocking findings
none

## Checks
- [x] Only owned paths changed. `src/api/context.ts` is not on the card but is necessary and correct: `Membership` feeds `mfaState()` (`context.ts:261`), whose `MfaMembership` now needs `sample`; the change is one query with `withSampleFlag` stripping the two columns so nothing new leaks into `memberships`. Inside backend-foundation's role paths; accept
- [x] Nothing outside scope (no web, no grace/lockout/exempt-procedure changes)
- [x] Tests exercise the behavior; none weakened (scan hits read above)
- [x] Tenancy: no new tables/`withSystem`; one query per membership load (no `isSampleWorkspace` per org); no email in new logs
- [x] Decisions: 0028 proposed (security-reviewer accepts), index row at README:41, links 0029

## Optional notes (not blocking)
- The generic `unhandledRejection` handlers log `errorData(reason)` (message + dev stack); a drizzle rejection's message quotes params. Same S-29 gap as `job failed`; keep on the security-reviewer's list.
- `auth-mail.ts:177` logs `String(err)` for SMTP failures; some servers echo the recipient. Author's own follow-up; fine.
- The `errorKind` unit test is the only check of `code` from a top-level `code` vs `cause.code`; it covers both via the two tests. OK.
