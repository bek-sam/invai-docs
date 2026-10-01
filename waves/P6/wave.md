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

## Metrics

## Retro
