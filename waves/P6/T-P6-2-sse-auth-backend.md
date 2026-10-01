# T-P6-2: `/events` drops `?token=`, re-checks the session every ping and closes revoked streams (B-31 backend)

| Field | Value |
|---|---|
| Wave | P6 |
| Scope ref | `always-in-scope: security` (v1-#4, S-30, S-G9: a session token in the URL lands in proxy and access logs; a revoked station token or floor session keeps receiving the shop's live events until the tablet reconnects) |
| Spec | backlog B-31; `invai-docs/security/v1-review.md` S-30; `invai-docs/research/12-security-quality-playbook.md` (session revocation) |
| Owner | backend-foundation |
| Reviewer | reviewer (sonnet) |
| Co-reviewers | security-reviewer (fable) |
| Risk flags | auth |
| Model | opus |
| Depends on | nothing (the floor already sends `Authorization: Bearer`, `invai-floor/src/realtime/sse.ts:88`) |

## Owned paths (edit)
- `invai-backend/src/api/events.ts`
- `invai-backend/src/api/events.test.ts` (new)

## Read-only paths
- `src/api/context.ts` (`buildContext`, `floorContext` already check revoked floor sessions, live station tokens and active membership), `src/modules/tenancy/floor-auth*`, `src/lib/realtime.ts`, `src/api/shutdown.ts`, `src/db/**` (T-P6-1), every other repo. If `context.ts` must change, stop and report.

## Interfaces promised
- On a failed re-check the server writes `event: unauthorized` with data `""`, unsubscribes, and ends the stream. A reconnect with the same credentials gets HTTP 401 `{"error":"unauthorized"}` (as today). T-P6-3 (floor) builds on exactly this name.

## Acceptance criteria
1. A request to `/events` with the session only in `?token=` (no `Authorization` header, no cookie) gets 401. The handler no longer reads `token` from the query. `Authorization: Bearer <floor session>` and the Better Auth cookie keep working; `Last-Event-ID` / `?lastEventId=` replay unchanged.
2. Given an open floor stream, when the owner revokes that station token (web Settings → Stations, or its oRPC procedure) or the floor session is signed out/revoked, or the member is deactivated, then within one ping interval (≤ 30 s; keep the 25 s ping) the server sends `event: unauthorized` and closes the stream; no further shop events reach that client.
3. A web user's cookie stream is re-checked the same way: after sign-out (session deleted) the stream closes within one interval.
4. The re-check reuses `buildContext` with the original request's credentials (no new auth logic), and a re-check whose company differs from the stream's company also closes it. A transient DB error during a re-check does not close a valid stream silently forever nor crash the process: decide (close and let the client reconnect is fine) and say which in the report.
5. The shutdown path (T-12-2: `shutdown` event, retry hint) is unchanged and still covered.
6. Tests in `events.test.ts`: query-only token → 401; header → 200 stream; revoked station token → `unauthorized` event and end (use a short injectable interval in tests, not a 25 s wait); still-valid session → keeps pinging. Each new test red on 471355a (say how you showed it).
7. Check `invai-web/src/lib/realtime.ts` (read-only): say in the report what the web does when its stream ends and the reconnect gets 401 (no tight reconnect loop expected; if there is one, report it, don't fix it).

## Verification
- `PORT=3150 REDIS_URL=redis://localhost:6379/10 pnpm dev:api` in `invai-backend` on the shared dev DB (read-only use: sign in, floor PIN; the station revoke in step 2 writes one row: create a **new** station token for the test and revoke that one, never the seeded Press 1 token in `seed-output.json`).
- Exercise for real with curl: `curl -N -H "Authorization: Bearer <floor session>" localhost:3150/events` stays open with pings; `curl -N "localhost:3150/events?token=<same>"` → 401; revoke the test station token as `owner@desertbloom.test` → the open curl prints `event: unauthorized` within 30 s and exits. Refused case: `presser@` cannot revoke tokens (FORBIDDEN).
- `pnpm typecheck && pnpm lint 2>&1 | tail -n 20`, `pnpm vitest run src/api/events.test.ts --reporter=dot 2>&1 | tail -n 20`, then the full `pnpm test 2>&1 | tail -n 20` once at the end (explicit 600000 ms timeout).

## Out of scope
- The floor change (T-P6-3), any web change, `context.ts`, rate limits, the realtime stream format, push-based revoke (pub/sub on revoke); the ping-interval re-check is the rule.

## Rules
- Role file `.claude/agents/backend-foundation.md`; run `threat-model-change` first (auth flag) and put its short result at the top of the report. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/backend-foundation/`.
- Other agents at the same time: backend-foundation on T-P6-1 (`src/db/reset.ts`, `src/db/seed/index.ts`) or T-P6-4 (`src/db/seed/**`), floor-engineer on T-P6-3 (`invai-floor`). Don't touch their files.
- Commit only your paths, attribution line at the end. **Don't push; only the tech lead pushes after the gate.** Foreground test runs only; don't end your turn with a run or a process going. Stop your API on :3150 (and its tsx watch parent) before you hand back. Record every PID you start and list it (stopped) in the report.
- Trim output (`2>&1 | tail -n 40`). Report (≤ 60 lines) to `invai-docs/waves/P6/reports/T-P6-2.md`, one line per milestone as you go.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
