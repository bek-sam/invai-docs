# T-P6-3: Floor sends its session only as a header and signs out on `unauthorized` (B-31 floor)

| Field | Value |
|---|---|
| Wave | P6 |
| Scope ref | `always-in-scope: security` (v1-#4, S-30, S-G9: the floor puts its session token in the `/events` URL) |
| Spec | backlog B-31; T-P6-2 interface (`event: unauthorized`, then 401 on reconnect) |
| Owner | floor-engineer |
| Reviewer | reviewer (opus) |
| Co-reviewers | security-reviewer (fable; one agent reviews T-P6-2 and T-P6-3) |
| Risk flags | auth, floor-correctness (a tablet that loses its session must land on sign-in, never keep showing stale work) |
| Model | sonnet |
| Depends on | T-P6-2 committed (its event name); the floor change is safe against the old backend too |

## Owned paths (edit)
- `invai-floor/src/realtime/sse.ts`, `invai-floor/src/realtime/sse.test.ts`
- The floor file that wires `connectSse` (`onUnauthorized` handler) only if needed for AC2; name it in the report.

## Read-only paths
- `invai-floor/src/lib/codes.ts` (its `?token=` is the station pairing QR, not this; leave it), `invai-floor/e2e/**` (QA's), every other repo.

## Acceptance criteria
1. `connectSse` never puts the session in the URL: the request URL is exactly `opts.url` (plus nothing token-related); the session goes only in `Authorization: Bearer`. The doc comment says so. `Last-Event-ID` behavior unchanged.
2. On an `unauthorized` SSE event the client stops (no reconnect loop) and calls `onUnauthorized` once, so the tablet goes to the same place it goes today on a 401 (the PIN/sign-in screen). A 401 on connect keeps its current handling and also stops retries.
3. Other events, `ping`, `ready` and `shutdown` (retry hint) behave as today.
4. Tests in `sse.test.ts`: URL has no `token=`; header present; `unauthorized` event → `onUnauthorized` called once and no further fetch; each new test red on b2cfd13 (say how you showed it). The existing test that asserts `?token=` is changed to the new rule (that is the requirement changing, not a weakened test; say so in the report).

## Verification
- `pnpm typecheck && pnpm lint && pnpm test 2>&1 | tail -n 20 && pnpm build 2>&1 | tail -n 5` in `invai-floor`.
- Exercise for real (if T-P6-2 is committed): backend at T-P6-2's commit on `PORT=3152 REDIS_URL=redis://localhost:6379/11`; floor `pnpm build && pnpm preview` against it (or the vitest fetch double if the floor CSP blocks a non-3000 API; say which); pair with a **new** test station token, revoke it as owner@ in web or by curl, and show the tablet returns to sign-in within 30 s. Screenshot at 1280×800 in en and es, and look at it. Stop everything you started.
- Floor E2E runs at the gate.

## Out of scope
- Backend and web changes, pairing QR format, offline outbox.

## Rules
- Role file `.claude/agents/floor-engineer.md`. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/floor-engineer/`.
- Other agents at the same time: backend-foundation on T-P6-4 (`invai-backend/src/db/seed/**`) and reviewers. Don't touch their files.
- Commit only your paths, attribution line at the end. **Don't push; only the tech lead pushes after the gate.** Foreground test runs only; don't end your turn with a run or a process going. Record every PID you start and list it (stopped) in the report.
- Trim output (`2>&1 | tail -n 40`). Report (≤ 60 lines) to `invai-docs/waves/P6/reports/T-P6-3.md`, one line per milestone as you go.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
