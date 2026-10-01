# Review of T-P6-2 (round 1)

- Reviewer: security-reviewer on fable (auth co-review)
- Author: backend-foundation on opus; commit invai-backend `5557014`
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| `git show 5557014 --stat` | only `src/api/events.ts`, `src/api/events.test.ts` |
| `pnpm vitest run src/api/events.test.ts --reporter=dot` | 1 file, 11 passed (3.85 s); the Vite-server exit warning is pre-existing |
| `grep -rn 'token=' invai-backend/src invai-floor/src invai-web/src` (minus email-link tokens) | no session-in-URL producer or consumer left; only the events test's negative cases and `codes.ts` pairing QR |
| `scan-test-weakening.sh invai-backend 471355a` | no hits |
| throwaway probe test (written, run, deleted; tree clean): `Authorization: Station <tok>`, `x-station-token`, anonymous + `Last-Event-ID` → `/events` | all 401 |
| read `context.ts:120-200`, `floor-auth.ts:106-262`, `ratelimit.ts:66-73`, `realtime.ts:31,120-126` | see checks |

## Acceptance criteria (security view)
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | handler copies only headers into `buildContext`; `?token=` → 401 on route and mounted app (tests); replay reads `lastEventId` only as a range start on `rt:company:<sessionCompany>` (`realtime.ts:121`), so a crafted id can't select another tenant's stream |
| 2 | yes | revoked station token (DB), `revokeFloorSession` (Redis), deactivated member (DB) all end with `event: unauthorized`, reconnect 401 (tests); `close()` unsubscribes before the final write so no shop event follows |
| 3 | yes | sign-out test; Better Auth has no cookie cache, so the DB sees the deleted session at the next re-check |
| 4 | yes | re-check is `buildContext` on the original headers; `companyId` and `sessionKind` must both match; other-company test closes; C1 test: failing probe → `shutdown` + `retry: 5000`, no `unauthorized`; `unauthorized` carries no `retry:` |
| 5 | yes | shutdown test unchanged, `retry: 1000` |
| 6 | yes | 11 tests; red-on-base claim is the primary reviewer's to re-run |

## Blocking findings
none

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope (`context.ts` untouched)
- [x] Tests exercise the behavior; none weakened
- [x] Tenancy: company compared on every re-check; stream, replay and subscribe keyed by the session's company; no `withSystem`; logs carry ids only (no token, no PII)
- [x] Fail-open/closed (C1): DB down → `shutdown` + retry (no mass lock-out). Redis down → `isRevoked` fails open with a warn log, so a signed-out floor session survives until the signed token's TTL; pre-existing for every request path, and station revoke and deactivation still close through the DB
- [x] Decisions: none needed (no contract change; C1/C2 recorded in `plan-architect.md`)

## Optional notes (not blocking)
1. `events.ts` recheck: a transient `buildContext` error (pool timeout) followed by a successful `select 1` reads as a revoke for that one stream; the tablet relocks and recovers by PIN. Distinguishing "context build failed" from "no session" needs `context.ts` (fenced). Backlog candidate, Low.
2. Connect path has no probe: a DB blip at (re)connect returns 401, which the new floor now treats as final (T-P6-3 AC2). Same effect as the existing queue-poll 401 → `onAuthFailure`, so not new, but a 503 when `buildContext` is anonymous **and** the probe fails would remove the last blip-looks-like-revoke path. Backlog candidate, Low, backend-foundation.
3. `dbProbe` has no timeout: a hanging DB stalls the ping loop (events still flow via the subscriber); proxies will cut the idle stream. Availability only.
