# Wave P6: floor live updates without a URL token and closed on revoke, safe db:reset, a seed that settles and repeats

- Status: **planned** (2026-10-01). Planned from the hand-off at the end of `waves/P5/wave.md`.
- Goal (user outcome): a station token or floor session that the owner revokes stops getting live updates within 30 s, and the floor no longer puts its session in a URL (S-30); resetting a scratch database can't wipe the shared queues or the shared `seed-output.json` again; two seeds give the same numbers, and the gate's sheet build no longer races the post-seed backlog (no more sub-80% golden-path sheets).
- Scope refs: always-in-scope for every card: B-31 (security: v1-#4, S-30, S-G9; pilot safety), B-219 (bug: dev queues wiped twice), B-249 + B-208 (bug: demo data shapes the product's numbers; flaky gate on the wedge).
- Owner's scope for this wave: only agent-doable P1/P2 items. Low (P3) items skipped. If none remain after P6, the tech lead writes `waves/status-2026-10-01.md` instead of a hand-off.
- Fences: no deploys, no AWS, no outbound sends. Track D out. OI-17 and OI-18 are not approved. `invai-infra` is read-only and never pushed (OI-22). Waves 24 and 25 stay paused (decision 0019). No buyer PII. No rate limit or security control weakened. Decision 0020 stands.
- Plan review: product-manager (scope), architect (design: the SSE revoke and `unauthorized` event in T-P6-2/3; the "settled seed" rule in T-P6-4). T-P6-1 starts at the same time as the plan reviews (owner's order: fix B-219 early); if a plan review changes it, it goes to round 2.

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| [T-P6-1](T-P6-1-safe-reset.md) `db:reset` refuses to wipe shared queues; seed refuses to overwrite the shared `seed-output.json` (B-219) | backend-foundation | sonnet | reviewer (opus) | none (dev tooling) | planned |
| [T-P6-2](T-P6-2-sse-auth-backend.md) `/events` drops `?token=`, re-checks the session every ping and closes revoked streams (B-31 backend) | backend-foundation | opus | reviewer (sonnet) + security-reviewer (fable) | auth | planned |
| [T-P6-3](T-P6-3-sse-auth-floor.md) Floor sends the session only as a header and signs out on `unauthorized` (B-31 floor) | floor-engineer | sonnet | reviewer (opus) + security-reviewer (fable, same agent as T-P6-2) | auth, floor-correctness | planned |
| [T-P6-4](T-P6-4-settled-deterministic-seed.md) Seed counts repeat run to run (B-249); the stack is settled before the gate builds sheets (B-208) | backend-foundation (seed) | opus | reviewer (opus) | floor-correctness (golden path) | planned |

Interfaces: T-P6-2 fixes the SSE event name before T-P6-3 starts: on a failed re-check the server writes `event: unauthorized` (data `""`) and ends the stream; a reconnect then gets HTTP 401. The floor already sends `Authorization: Bearer`, so the backend change is safe against a cached old floor (it also sends the header) and the floor change is safe against the old backend. No shared files: T-P6-1 owns `src/db/reset.ts`, `src/db/reset.test.ts` and `src/db/seed/index.ts`; T-P6-2 owns `src/api/events.ts` + a new test; T-P6-4 owns `src/db/seed/**` only after T-P6-1 has committed.

Order: T-P6-1 + plan reviews (PM, architect) → T-P6-2 → T-P6-3 (after T-P6-2's commit) and T-P6-4 (after T-P6-1's commit). Max 3 agents at once, reviewers included; max 2 heavy test runs (T-P6-4's seeds count as heavy).

## Slots and ports
- T-P6-1: scratch DB `invai_p6_reset`, Valkey DB 13, `SEED_OUTPUT_FILE=/tmp/p6-1-seed-output.json`; no imaging needed (no full seed). Drop the DB at the end.
- T-P6-2: API :3150, Valkey DB 10, shared dev DB read-only (sign-in and floor PIN only).
- T-P6-3: vitest only; any live check uses T-P6-2's committed code on API :3152, Valkey DB 11.
- T-P6-4: scratch DBs `invai_p6_seed_a`, `invai_p6_seed_b`, imaging :8031, Valkey DB 12, `SEED_OUTPUT_FILE=/tmp/p6-4-seed-output.json`, worker with the same `REDIS_URL`. Drop DBs at the end.
- Gate slot (:3000, :5173, :5174, :8000) stays free. Orphan P4 APIs on :3141-3143 (PIDs 4218, 4221, 4222 + watchers 64192, 52296, 11838, 11830) stopped by the P6 tech lead before the wave.

## Integration gate
- [ ] `pnpm gate invai-backend invai-floor` (+ `invai-web` only if a card touched it)
- [ ] Tech lead looked at the floor live-update screen after a revoke and the seed count comparison
- [ ] Pushed (bare `git -C <repo> push origin main`); invai-infra not pushed (OI-22)

## Build log
- 2026-10-01 (P6 tech lead) Pre-wave: disk 9.4 GB free; docker healthy; code repos clean at origin/main (contracts d6d038b, backend 471355a, web 0ad173d, floor b2cfd13, ui 2e3519d); infra has 5 local commits (OI-22, not pushed). Stopped the orphan P4 APIs on :3141-3143 and their `pnpm dev:api` watchers (owner's order); ports 3000-3199 free.
- 2026-10-01 Plan committed (docs 283e47b). Started T-P6-1 (backend-foundation, sonnet), the PM scope review (sonnet) and the architect design review (opus) together.
- 2026-10-01 PM plan review: approve (`reviews/plan-pm.md`, docs 8d24ce1). Agent-doable non-Low items left after P6: B-134 (shared ConfidenceBadge in invai-ui, T-23-4 never started), B-115 (guard-bash.py gaps; platform-sre, hook paths). These go to the P7 hand-off.
- 2026-10-01 Architect plan review: approve-with-changes (`reviews/plan-architect.md`, docs fb9c926, 0cdb194). R1: no contract change; web EventSource reconnects once, gets 401, closes (no loop). C1 added to T-P6-2 AC4 (probe `select 1` before sending `unauthorized`, else end with retry hint; no `retry:` on `unauthorized`); C2 timing ≤ 30 s one instance / ≤ 55 s across. R2: B-208 fix in the seed (run QA and pending renders inline before `releaseOutbox`), added to T-P6-4 AC6. R3: no caller breaks; guard placement notes added to T-P6-1 AC5 after its start (reviewer checks; round 2 if missing). Started T-P6-2 (backend-foundation, opus).
- 2026-10-01 T-P6-1 built: backend fb424fe (`assertSafeToReset` in reset.ts main path, `assertSafeToSeed` first line of seed `main()`, main guard around the seed's `main()` so tests can import it; 19 tests; refusals exercised on scratch DB, DB 0 untouched). Report docs effddbb. Open question for the reviewer: seed guard checks MIGRATION_DATABASE_URL only (R3 asked for both URLs). Started the T-P6-1 reviewer (opus) and T-P6-4 (backend-foundation, opus; from fb424fe, Valkey DB 12, imaging :8031).
- 2026-10-01 T-P6-2 built: backend 5557014 (no `?token=`; re-check per 25 s ping via `buildContext`; `unauthorized` without retry, or `shutdown` + `retry: 5000` when the `select 1` probe fails; 11 tests, 8 red on 471355a; full suite 1472 passed). Live :3150: revoked test token closed the curl in 22 s, web sign-out in 23 s, query-only 401, presser@ 403; web reconnects once then shows closed (AC7). Left one revoked test station "T-P6-2 SSE test" in the dev DB (gate reseed clears it). Started T-P6-3 (floor-engineer, sonnet; live API :3152, Valkey 11). T-P6-2 reviews queue for a slot.
- 2026-10-01 T-P6-1 reviewer r1 (opus): changes-required (`reviews/T-P6-1-reviewer-r1.md`, docs 5069865): the seed guard checks only `MIGRATION_DATABASE_URL`; with `DATABASE_URL` on a scratch DB and no `SEED_OUTPUT_FILE` it passes (proved). Reset half of R3 met; 19 tests, 5 red with guards removed; refusals re-exercised on a scratch DB. Round 2 queued until T-P6-4 commits, because T-P6-4 owns `src/db/seed/**` now (no two owners of `seed/index.ts`). Started the T-P6-2 reviewer (sonnet); the security-reviewer (fable) will review T-P6-2 and T-P6-3 together.
- 2026-10-01 T-P6-3 built: floor 9304da1 (session only as Bearer; `unauthorized` or 401 stops retries and calls `onUnauthorized` once; on b2cfd13 a 401 retried 592 times in 1 s; 114 tests + build). Live on :3152 + floor dev with proxy: revoke → station-removed screen in 23.4 s, en and es. Grant recorded after the fact: `invai-floor/README.md` (floor-engineer's own repo; doc line on the header-only session). It used :5174 briefly (gate slot; stopped, port free). Started the security-reviewer (fable) on T-P6-2 + T-P6-3; the T-P6-3 reviewer (opus) queues for a slot.
- 2026-10-01 Security-reviewer r1 (fable): approve both (`reviews/T-P6-2-security-reviewer-r1.md`, `T-P6-3-security-reviewer-r1.md`, docs b0313c0): no session-in-URL producer or consumer left in backend/floor/web; every revoke path closes with `unauthorized`; replay is keyed by the session's company; probe failure gives `shutdown`, never `unauthorized`; the floor stops on `unauthorized`/401 with no loop. Low notes (backlog): the connect path has no probe, so a DB blip at reconnect gives 401 and the new floor relocks (PIN recovers; suggested backend 503 when anonymous and probe fails); `dbProbe` has no timeout. Started the T-P6-3 reviewer (opus).
- 2026-10-01 T-P6-3 reviewer r1 (opus): approve (`reviews/T-P6-3-reviewer-r1.md`, docs a10e68b): 114 tests; all 3 sse tests red on b2cfd13 (401 retried 596 times); shutdown/503/network errors still reconnect and never sign out; `?token=` test replaced by stricter checks. Note (Low, backlog): after `unauthorized` the parser keeps reading, so a second `unauthorized` would call `onUnauthorized` twice (the backend sends one and closes). A plain `pnpm build` needs `VITE_API_URL` set (existing vite.config check; the gate sets it). **T-P6-3 approved** (reviewer + security).
- 2026-10-01 T-P6-2 reviewer r1 (sonnet): approve (`reviews/T-P6-2-reviewer-r1.md`, docs d987327): 11 tests; 8 of 11 red on 471355a; dropping the C1 probe check fails its test; live sign-out → `unauthorized`, no `retry:`, 401 on reconnect. Its first full-suite run had 2 failures that didn't reproduce on rerun (watch at the gate). **T-P6-2 approved** (reviewer + security).

## Metrics

## Retro
