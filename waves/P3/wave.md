# Wave P3: the floor rate-limit fix, one gate, push P1 + P2 + P3

- Status: **building** (2026-10-01). Planned from the hand-off at the end of `waves/P2/wave.md`.
- Goal (user outcome): a busy floor never gets a scan rejected because thumbnails used up the shop's write allowance; if the server does say "slow down", the presser sees "busy", not "offline". Then P1, P2 and P3 pass one gate and are pushed.
- Scope refs: always-in-scope (bug) for T-P3-1 (B-236, High) and T-P3-2 (B-237). Slots 3–5 from the backlog's agent-doable P1/P2 items, PM-ranked, after the gate.
- Fences: no deploys, no AWS, no outbound sends. Track D out. OI-17 and OI-18 are not approved. `invai-infra` is read-only and never pushed (OI-22). Waves 24 and 25 stay paused (decision 0019). No buyer PII. No rate limit is raised or lowered.
- Plan review: architect (design of T-P3-1/2) runs alongside the builders, as P2 did for its gate fixes (both are always-in-scope bugs from a confirmed root cause). PM ranks slots 3–5.

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| [T-P3-1](T-P3-1-rate-bucket-by-intent.md) Rate-limit buckets by intent (B-236) | backend-foundation | sonnet | reviewer (opus) + security-reviewer (opus) | auth, floor-correctness | **approved r1** (backend b5c649f) |
| [T-P3-2](T-P3-2-floor-busy-state.md) Floor shows 429 as busy; fewer signed URLs (B-237) | floor-engineer | sonnet | reviewer (opus) | floor-correctness, ui (copy) | **approved r2** (floor 0dd01ee, 5389e5f; QA e2e 8ed8ad3) |
| [T-P3-3](T-P3-3-es-money-grouping.md) es money: thousands separator on 4-digit amounts | product-designer | sonnet | reviewer (opus) | ui | queued (after push) |
| [T-P3-4](T-P3-4-losing-orders-units.md) Losing orders Units 0 / Revenue $0 (B-230, verify first) | backend-engineer (analytics) | sonnet | reviewer (opus) | none | queued (after push) |
| [T-P3-5](T-P3-5-market-test-cache-leak.md) Market tests stop leaking cache rows (B-221) | backend-engineer (market) | sonnet | reviewer (sonnet) | none | queued (after push) |

## Slots and ports
- T-P3-1: API :3136, Valkey DB 13. T-P3-2: API :3137, floor dev :5184, Valkey DB 14.
- Gate slot (:3000, :5173, :5174, :8000) stays free for `pnpm gate`.
- Pre-wave checks (2026-10-01): disk 5.3 GB free; :3000 free; test Valkey DB 15 has no clients; trees clean except untracked `.DS_Store`/`.claude/`. Leftover test DBs `invai_test_t230`, `invai_test_23037` (not this wave's): drop at the gate if no connections.

## Integration gate
- [x] `pnpm gate invai-backend invai-imaging invai-floor invai-web` passed on a fresh seed (run 2, log `invai-infra/.gate/run-20261001T050953Z.log`): backend 1387, imaging 119, floor 112 + build, web 136 + build, API golden path 13/13, web e2e 34, floor e2e 3
- [x] Tech lead looked at the floor busy screenshots (`/tmp/p3-floor/`): wrong blank stays red BLOCKED while busy ("Checked on this tablet. Busy — confirming in 1 s."); amber OCUPADO panel in es. The es shot predates the r2 copy fix (unit-tested). Minor: the es header pill "1 escaneo por sincronizar" wraps to two lines at 1280 px (B-241)
- [ ] Pushed to `main`: P1, P2 and P3 commits together (backend, imaging, floor, web, docs); never `invai-infra`

## Build log
- 2026-10-01 Plan and cards T-P3-1, T-P3-2 written. Started: T-P3-1 (backend-foundation), T-P3-2 (floor-engineer), architect plan review (3 agents).
- 2026-10-01 Architect plan review: approve-with-changes (`reviews/plan-architect.md`). Reads set in the backend confirmed; contract `rateBucket` is B-240 (later). Its must-stay-writes list is added to T-P3-1 for the reviewers. Ruling R1 for T-P3-2 (a late result only replaces the panel when its `clientScanId` matches the scan on screen) added to the card as a queued ruling: checked at review, round 2 if missing (lesson 2026-10-01: no ACs into a running card).
- 2026-10-01 PM plan review: approve T-P3-1/2 (`reviews/plan-pm.md`); ranked slots 3–5: es money grouping (invai-ui), B-230, B-221 (`product/backlog-ranking.md`). Cards T-P3-3..5 written; they start after the P1+P2+P3 push so no unreviewed commit stacks on the gated ones (lesson 2026-09-30 W23). Waiting: B-238+B-224, B-231, B-132 (architect first); B-235, B-239, B-232, B-234 (filler).
- 2026-10-01 T-P3-1 builder: AC4/AC5 exercised (report in progress). It killed PID 31268 by mistake (an API on :3142 from another session, not this wave's; same command line as its own child). Not restarted (env unknown). Retro item: identify own PIDs by port (`lsof -p`) before kill, not by command line.
- 2026-10-01 T-P3-1 built: backend b5c649f (`NON_GET_READS` = files.downloadUrl, skuRules.test, skuRules.suggest; the other 18 non-GET read-permission procedures stay writes; `src/api/buckets.test.ts` walks the contract). Live: 150 downloadUrl left tb:writes absent, then scan 200; drained reads → 429 + Retry-After. Full suite 1387 passed (one known shipping load flake, passes alone). Reviewer (opus) and security-reviewer (opus) started.
- 2026-10-01 T-P3-1 security r1: approve (`reviews/T-P3-1-security-reviewer-r1.md`; the 3 moved procedures have no side effects; the bucket comes from the contract, not the request; downloadUrl checks the company prefix before the exists check; limits untouched). Note: if `skuRules.suggest` ever honours `useAi`, it leaves the reads set.
- 2026-10-01 T-P3-1 reviewer r1: approve (`reviews/T-P3-1-reviewer-r1.md`; pinning test broken 3 ways in /tmp, red each time; inventory.suppliers.stock and shipping.batchLabelPdf rightly stay writes; live 130 downloadUrl on :3139 left writes untouched). Notes: `skuRules.suggest` useAi guard → B-240 note; the dev DB's station token no longer matches `seed-output.json` (the gate reseeds).
- 2026-10-01 T-P3-2 built: floor 0dd01ee (429 is its own `busy` kind with retryAfterSec, never parks; amber BUSY/OCUPADO panel; late server answer replaces the panel only for the same clientScanId (R1); thumbnail in-flight de-dupe, no failure cache, expiry −30 s: 45 thumbnails → 26 calls, was 45). floor 109 tests + build. Reviewer (opus) started.
- 2026-10-01 Gate started early (PID 36722, out `/tmp/p3-gate.out`) while T-P3-2 review runs, on backend b5c649f / floor 0dd01ee; a T-P3-2 round 2 means a re-run. Pre-check: gate ports free, Valkey DB 15 no clients, trees clean; dropped stale `invai_test_32610` (T-P3-1's killed duplicate run) and `invai_test_t230` (0 connections). Disk 6.5 GB.
- 2026-10-01 T-P3-2 reviewer r1: changes-required (`reviews/T-P3-2-reviewer-r1.md`): floor correctness and R1 hold (9 new tests red on base), but every online press scan applies its result and sound twice (resolved published for live sends too). Non-blocking folded into round 2: resolved entries never cleared; es busy copy says "retry"; rejected alert says offline for busy. Gate stopped (my PIDs 36730, 36850; trap cleaned up; no leftover DBs) since round 2 edits floor. Round 1 builder had already stopped. Round 2 started (floor-engineer).
- 2026-10-01 T-P3-2 r2: floor 5389e5f (resolved result applied only while provisional/queued; one-sound test; resolved pruned after 2 min and cleared on Next/unmount; es busy copy says it retries itself; rejected alert says "queued"/"guardado" in both). floor 112 tests + build. Blocked: QA's `e2e/offline.spec.ts:89` asserts the old alert text. Started: QA (haiku) one-line e2e copy update; reviewer r2 (opus), which also checks the QA commit (lesson 2026-09-28: gate-time QA test edits get a reviewer pass).
- 2026-10-01 QA: floor 8ed8ad3 (`e2e/offline.spec.ts:89` expects "1 queued scan was rejected"; text only). Reviewer r2 checks it.
- 2026-10-01 T-P3-2 reviewer r2: approve (`reviews/T-P3-2-reviewer-r2.md`; one-sound test red on 0dd01ee with tick,error,error; pruning can't drop a pending result; QA 8ed8ad3 exact string, same matcher). Gate run 2 started.
