# Wave P6 — floor live updates without a URL token, safe db:reset, a seed that settles and repeats

**Dates:** 2026-10-01.

## What was built
- **T-P6-1** `db:reset` refuses to wipe shared queues; seed refuses to overwrite the
  shared `seed-output.json` (B-219) (backend-foundation) — the mechanical fix for the
  mistake that had hit the project at least four times by this point (waves T-23-9, P5,
  and earlier).
- **T-P6-2** `/events` drops `?token=`, re-checks the session every ping and closes
  revoked streams (B-31 backend) (backend-foundation) — a station token or floor session
  the owner revokes now stops getting live updates within 30 seconds.
- **T-P6-3** Floor sends the session only as a header and signs out on `unauthorized`
  (B-31 floor) (floor-engineer) — the client half: no session token sits in a URL anymore
  (S-30), where it could leak through logs, browser history or a referrer header.
- **T-P6-4** Seed counts repeat run to run (B-249); the stack is settled before the gate
  builds sheets (B-208) (backend-foundation/seed) — two seeds now give the same numbers,
  and the gate's gang-sheet step no longer races the post-seed backlog.

## Why
A revoked station token or floor session that keeps receiving live updates is a real
security gap — someone who should no longer have access keeps seeing production data in
real time. And a non-deterministic seed (different counts on every run) had been quietly
undermining every other wave's "re-run this and confirm the numbers" verification step.

## What went wrong
- Two full gate runs failed for a reason nobody suspected at first: tests ran 142 seconds
  and 681 seconds against only a 30-second limit, and `db:reset` deadlocked mid-run,
  leaving the dev DB half-reset. The actual cause: the Mac had gone into idle sleep
  mid-run (confirmed in `pmset -g log`, two separate sleep windows), which stalled timers
  and database connections for however long the machine was asleep.

## What the team learned
- Run the gate under `caffeinate -i` to stop the Mac from sleeping mid-run; before
  calling a timing failure a product bug, check `pmset -g log` for a Sleep entry in the
  failure window — a silent system sleep looks exactly like a slow test or a hung
  database until you check.
- This closes the loop on the shared-Redis/seed-safety saga from waves T-23-9 and P5:
  B-219 finally lands as a mechanical refusal (not just a rule to remember), the same
  pattern the shared-test-DB problem followed in wave A2.

## Files to look at
- `invai-backend/scripts/db-reset.ts` (or wherever `db:reset` lives), `src/db/seed/` — T-P6-1.
- `invai-backend/src/api/events.ts` (`/events` SSE route) — token removal, session
  re-check (T-P6-2).
- `invai-floor/src/api/rpc.ts` (session header, sign-out on `unauthorized`) — T-P6-3.
- `invai-backend/src/db/seed/builder.ts` — deterministic counts, settled-before-build
  (T-P6-4).
- `invai-docs/team/lessons.md` (2026-10-01, "wave P6" row — the Mac-sleep incident).
