# Wave P1: polish and bugs (test isolation, flakes, imaging, AI, thumbnails, floor QC banner)

- Status: **all 5 cards approved; gate blocked** (2026-09-30). Nothing pushed. See "Hand-off" at the end. Planned from the hand-off in `waves/24/wave.md`.
- **Folder name:** this polish wave was handed off inside `waves/24/`, whose cards T-24-1..4 are the paused deploy-prep wave (decision 0019, until the owner starts the AWS setup). To keep the two apart, the polish wave lives in `waves/P1/` with cards `T-P1-<k>`. `waves/24/` stays the deploy-prep wave, paused, and is not run.
- Goal (user outcome): agents and the gate can run backend tests at the same time without wiping each other; the gate no longer fails on two known load flakes; designs and order items show real thumbnails; sheets report true film use and are print-ready (ICC, mirror, bounds); the assistant's answers read cleanly in both languages; the Spanish QC result says what happened.
- Scope refs: always-in-scope (bug, reliability for pilots) for T-P1-1, T-P1-4, T-P1-5; `product/scope.md#mvp-in` items 4, 12 (T-P1-2), 13, 16 (T-P1-3).
- Fences: no deploys, no AWS, no outbound sends. Track D (B-178..B-181) stays out. OI-17 and OI-18 are not approved. No buyer PII in fixtures, screens or AI prompts. `invai-infra` is read-only for every card (it holds unpushed T-23-6, T-23-7, T-24-1 commits; OI-22 open).
- Plan reviewed by: product-manager (2026-09-30, approve, `reviews/plan-pm.md`), architect (2026-09-30, approve-with-changes, `reviews/plan-architect.md`; rulings 1 and 5 applied).

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| [T-P1-1](T-P1-1-test-db-per-run.md) Per-run test DB and Redis DB (B-228, absorbs B-215), market retry test on fake timers (B-229 part 1) | backend-foundation | sonnet | reviewer (opus) | test infra | **approved r2** (backend 5649c7c, f5c0a68) |
| [T-P1-2](T-P1-2-imaging-polish.md) Imaging polish (T-23-3: B-103 rest, B-41) plus a `/preview` thumbnail endpoint for T-P1-4 | imaging-engineer | sonnet | reviewer (opus) + security-reviewer | files | **approved r2** (imaging 2fc3806, f77e6e8, 26699d8) |
| [T-P1-3](T-P1-3-ai-market-polish.md) AI and market polish (T-23-4: B-114, B-131, B-132, B-135, B-165, B-192) plus the publish concurrency test (B-229 part 2) | ai-engineer | sonnet | reviewer (opus) | ai | **approved r2** (backend b81a038, c9fa1e5; AC3 B-132 to backlog) |
| [T-P1-4](T-P1-4-design-thumbnails.md) Design and order-item thumbnails (B-209) | backend-engineer (catalog) | sonnet | reviewer (opus) + security-reviewer | files | **approved r1** (backend 7247b32) |
| [T-P1-5](T-P1-5-floor-qc-banner.md) Floor QC result banner in Spanish (B-222) | floor-engineer | sonnet | reviewer (opus) | ui (copy only) | **approved r1** (floor ef1d926) |

Co-reviewers (decision 0019): `security-reviewer` (sonnet) for T-P1-2 and T-P1-4 (`files` flag; architect ruling 5). No other co-reviewers: no contract change, no migration, no new screen, and the ai-engineer owns its own prompts.

## Agreed interfaces (fixed by this plan; change only through the tech lead)
- **Imaging `POST /preview`** (T-P1-2 provides, T-P1-4 consumes): request `{ file_key: Key, out_key: Key, max_px: int = 512 (64..2048) }`; reads the source PNG/JPEG/PDF-first-page from storage, writes an sRGB PNG whose longest side is at most `max_px` (never upscaled), returns `{ out_key, width_px, height_px }`. Same auth as the other non-dev routes (shared secret). 422 on bad input. T-P1-2 commits this endpoint (with a test) **first**, before the rest of its card, and says so in its report.
- **Backend imaging client** `imaging.preview({ file_key, out_key, max_px? }) -> { out_key, width_px, height_px }` (snake_case like every other method in `client.ts`, architect ruling 1) with a mock that copies or synthesizes a small PNG when imaging is unavailable (as the other client methods do). Written by T-P1-4 under a grant (below).
- **Test DB naming** (T-P1-1): unless `TEST_DATABASE_URL` is set, each `vitest` run uses `invai_test_<pid>` (created from a migrated template `invai_test_tpl`), and unless `REDIS_URL` is set, a free Redis DB from 1–14 claimed with a lock key. Explicit env vars always win, so the gate and CI keep working unchanged.

## Order and file split
- Step 1 (3 agents): PM and architect plan reviews; T-P1-1 build (test infra first, so every later card's test runs are isolated).
- Step 2: T-P1-2 imaging (no backend dependency) and T-P1-5 floor (tiny), as slots free. T-P1-1's review.
- Step 3: T-P1-3 AI after T-P1-1 commits (backend tests). T-P1-4 after T-P1-1 commits **and** T-P1-2's `/preview` commit.
- Until T-P1-1 is committed, any backend test run pins its own DB and Redis DB (`team/agent-brief.md`).
- Shared repo `invai-backend`: T-P1-1 owns `src/test/**`, `src/env.ts` (test URL logic only), `vitest.config.ts`, `package.json` (test scripts only) and the market test file; T-P1-3 owns `src/ai/**`, `src/modules/ai/**`, `evals/**` and the B-131 grant; T-P1-4 owns `src/modules/catalog/**` and its grants. No two cards share a file.

## Grants (tech lead)
- T-P1-1 (backend-foundation): `invai-backend/src/integrations/market/http.test.ts` only (fake timers; integrations-engineer's path, test file only, no product code).
- T-P1-3 (ai-engineer): `invai-backend/src/modules/market/signals.ts` and `compute.ts` (+ their tests) for B-131 only (carried from T-23-4).
- T-P1-4 (backend-engineer): `invai-backend/src/integrations/imaging/client.ts` (+ test), the `preview` method and its mock only; `invai-backend/src/modules/orders/mapping.ts`, the `artworkPreviewKey` assignment only; `invai-backend/src/db/seed/**`, only the lines that set `design_files.preview_key` (and order-item preview keys) for seeded designs.

## Not in this wave (follow-on wave P2, or backlog)
- B-227 `db:reset` 40P01 deadlock (platform-sre, Low): no recurrence in A2's three gate runs. Backlog; investigate if it recurs.
- B-230 losing orders Units 0 / Revenue $0 (backend-engineer finance, verify), B-223, B-224, Today actions jobId re-queue after 3 failures, D2 "unmapped" label under es, a D13 fixture shop with fixed costs, invai-ui follow-ups (PageHeader 390 px clip, StatCard neutral, KpiTile truncation, top action priority, es group separator): wave P2 candidates.
- Paused, not run: T-24-1..4 (`waves/24/`) and T-25-1..5 (`waves/25/`), decision 0019. T-24-1's infra commit `3dbb899` stays unpushed until S-45 round 2.
- Owner-only: real-model eval of prompt v6 (as-042), needs the owner's key.

## Integration gate
- [ ] (REFUSED 2026-09-30: port 3000 held by PID 91824, a `pnpm dev:api` (parent 56757) running for about 6 h that this wave didn't start; the tech lead doesn't kill other processes) `pnpm gate invai-backend invai-imaging invai-floor` (plus `invai-web` only if a card changed it; never `invai-infra`) passes on a fresh seed: repo checks, API golden path, browser e2e, floor e2e
- [ ] Two backend `pnpm test` runs started at the same time both pass (T-P1-1's acceptance, re-checked at the gate)
- [ ] Tech lead looks at /catalog/designs (thumbnails) and the floor QC result in Spanish
- [ ] Pushed to `main` (never `invai-infra`)
- If Docker or Valkey hangs during the gate: record it here and stop, rather than looping.

## Build log
- 2026-09-30 Plan and cards written (T-P1-1..5). Plan reviews (PM, architect) and T-P1-1 started.
- 2026-09-30 PM plan review: approve (B-131 spec Step 3a is ready).
- 2026-09-30 T-P1-5 (floor) started.
- 2026-09-30 Architect plan review: approve-with-changes. Applied: ruling 1 (snake_case `imaging.preview`), ruling 5 (security-reviewer co-reviews T-P1-2 and T-P1-4). Rulings 2–4 confirm the test-DB design, ownership split and T-P1-4 grants.
- 2026-09-30 T-P1-2 (imaging) started; /preview to be committed first.
- 2026-09-30 T-P1-5 built: floor ef1d926 (typecheck, lint, 100 tests, build green; es screenshot shows APROBADO). Review started: reviewer (opus).
- 2026-09-30 T-P1-5 reviewer r1: approve (`reviews/T-P1-5-reviewer-r1.md`). Note: floor `pnpm build` needs VITE_API_URL set (existing config check; gate sets it).
- 2026-09-30 T-P1-3 (AI) started before T-P1-1 committed, on a pinned test DB (invai_p13_test, Redis 13).
- 2026-09-30 T-P1-2 built: imaging 2fc3806 (`/preview`, AC0) and f77e6e8 (ICC, mirror, flags, B-41); ruff clean, pytest 117. Deviation: AC4 film use is on `/nest` (it sees the whole sheet set), not `/compose`. Tech lead ruling: accepted as the card's intent (additive field on the set response); the reviewer checks it is additive. Review started: reviewer (opus); security co-review when a slot frees.
- 2026-09-30 T-P1-2 reviewer r1: changes-required. `/render/personalization` now returns new flag codes (`upscale`, `aspect_mismatch`) that the backend client's fixed flag list rejects ("unexpected response shape"), so an upscaled buyer photo would fail for good. Tech lead ruling: fix in imaging. The new flags are opt-in through a request field, default off, so the response is unchanged for today's callers. No contract change in this wave. Wiring the flags into contracts and backend goes to the backlog (architect, then integrations-engineer). Round 2 started (imaging-engineer).
- 2026-09-30 T-P1-2 r2: imaging 26699d8 (opt-in `photo_flags`, default response unchanged; pytest 119). Reviewer r2 started.
- 2026-09-30 T-P1-2 reviewer r2: approve (real backend client parses default responses; follow-up: widen contract flag enum + client.ts:74-81 before sending photo_flags). Security co-review started.
- 2026-09-30 T-P1-2 security r1: approve. Imaging trusts the backend for company prefixes (S-11/S-12 model), so T-P1-4 must check `isCompanyKey` on both keys (added as T-P1-4 AC7 before launch). Low follow-up (backlog): `/preview` isn't in imaging's HEAVY_PATHS concurrency limiter, and embedded ICC profiles have no size cap.
- 2026-09-30 T-P1-4 (thumbnails) started on a pinned test DB (invai_p14_test); own imaging :8054, API :3154.
- 2026-09-30 T-P1-1 built: backend 5649c7c (per-run DB from template under an advisory lock, Redis DB claim 1–14, provide/inject to workers, B-215 decoded-name guard, market test on fake sleep). AC7: two unpinned full runs at once both passed, no leftovers. Late grant (recorded on the report): `invai-backend/.env.example`, testing comment lines only (backend-foundation's env config; card gap, tech lead's). Full-suite runs each hit one different load flake outside the card (assistant-tools while T-P1-3 edited the shared tree; shipping concurrent batchBuy); watch at the gate. Review started: reviewer (opus).
- 2026-09-30 T-P1-3 built: backend b81a038 (B-131, B-192, B-135 backend side, B-165, B-229 part 2; B-114 was already fixed, so a regression test was added; 276 tests, publish 5/5). AC3 (B-132) is not met: the root cause is in `@orpc/client`'s event iterator (a dependency), so it goes back to the backlog for an architect decision (patch or keep the QA allow-list). Out-of-card findings for the backlog: the pre-v6 analytics tools answer in English under es; a full eval run exhausts the eval tenant's trial credits. Review started: reviewer (opus).
- 2026-09-30 T-P1-4 built: backend 7247b32 (preview job on attach or replace, `imaging.preview` with mock, isCompanyKey on both keys, seed sets previews, mapping copies the design preview; 70 tests). Live: dev designs went from 0 to 40/40 previews (left in place as evidence), a 154x512 PNG, presser refused 403, a replaced file cleared its preview then re-rendered in 4 s. AC3 partial, which the card allows: items mapped before their design's preview is ready stay empty until remapped. A subscriber in orders/jobs.ts is the follow-up (backlog). Review started: reviewer (opus); security co-review when a slot frees.
- 2026-09-30 T-P1-4 reviewer r1: approve. The order drawer falls back to the design preview, so the AC3 gap doesn't show. Backlog follow-ups: any imaging error (not only imaging down) writes a permanent gray placeholder; no test covers AC2 or AC3; old preview objects are left behind on replace; the job holds a DB transaction during the imaging call (same pattern as the QA job). Security co-review started.
- 2026-09-30 T-P1-3 reviewer r1: changes-required: (1) AC1 past act-by date when 0 < weeks-to-peak < lead time (assistant-tools.ts:1034); (2) AC5 the assistant eval seed's second tenant isn't deleted (evals/assistant/seed.ts:38); (3) B-131 regression: an all-zero series returns a flat index instead of null (signals.ts:230-244), so the Census fallback never runs. B-132 confirmed outside owned paths → backlog. Round 2 started (ai-engineer).
- 2026-09-30 T-P1-4 security r1: approve (AC7 enforced on the job path; Low hardening note: the seed calls imaging.preview directly with trusted keys, so it should use renderDesignPreviews for consistency, backlog). T-P1-4 done.
- 2026-09-30 T-P1-1 reviewer r1: changes-required. `test-redis.test.ts` works on the real DB-15 claim list: its afterEach deletes every claim (`KEYS` + `DEL`), asserts the list is empty, and fills all 14 slots for 60 s. That breaks live parallel runs (AC2, AC7). Everything else passed: two concurrent 1368-test runs, AC3, AC5, AC6. Round 2 started (backend-foundation).
- 2026-09-30 Coordinator asked who is editing T-P1-3's files after b81a038. It is the T-P1-3 round 2 builder (ai-engineer), the only writer, fixing the three r1 findings. The round 1 builder's last background full-suite run (1368 passed) has finished, and it has no live work left. The round 2 diff goes to the reviewer (r2) before the gate.
- 2026-09-30 T-P1-4 builder's last full suite: 1368 passed, 2 failed, both in T-P1-3 round 2's in-flight files (assistant-tools B-192, engine B-131 all-zero). These are round 2's new tests, written to fail before its fix as the round 2 prompt asked. They're not a T-P1-4 defect. Single writer: the T-P1-3 r2 ai-engineer. Also in flight: T-P1-1 r2 (src/test/test-redis*).
- 2026-09-30 T-P1-1 r2: backend f5c0a68 (registry prefix is a parameter; the test uses its own prefix). Two concurrent full runs: DB-15 claims never hit zero in 152 polls. One known Postgres load flake (`tuple concurrently updated`, reference/index.test.ts; stale sweep), passed alone. The builder also committed its own report in invai-docs (89f616e, that file only; harmless, but reports go in with the wave docs). Reviewer r2 started.
- 2026-09-30 T-P1-1 reviewer r2: approve. The stale sweep can't drop a live run's DB (dead pid + 1 h marker, under one advisory lock). The flake is in the test itself (`test-db.test.ts:99-105` uses a fixed fake DB outside the lock; backlog). AC8 applied: the `team/agent-brief.md` Tests rule now says plain runs isolate themselves.
- 2026-09-30 T-P1-3 r2: backend c9fa1e5 (all 3 findings fixed, each test red before the fix; 278 targeted tests, full suite green, evals clean, dev companies 5 before and after). Reviewer r2 started.
- 2026-09-30 Coordinator: backend HEAD (f5c0a68 + c9fa1e5) passes the full chain, 1370 tests, exit 0. Pre-gate check: infra healthy; disk 6.4 GB free (OI-20); node on :3000 (PID 91824) and :3142 (PID 91823) aren't from this wave's agents, and the gate refuses rather than fights.
- 2026-09-30 T-P1-3 reviewer r2: approve. All 5 cards approved. Gate started.
- 2026-09-30 Gate run 1: `GATE REFUSED: port 3000 is already held by pid 91824 (a dev stack this gate did not start)`. This wasn't a Docker or Valkey hang (infra is healthy), but per the run order the tech lead records it and stops rather than kill another process or loop. Nothing pushed.

## Metrics
- First-pass approval: 2/5 (T-P1-4, T-P1-5 approved in round 1 by every reviewer). T-P1-1 r2 (its own Redis unit test wiped the live claim list), T-P1-2 r2 (new flag codes broke the backend client), T-P1-3 r2 (3 findings). No card needed a third round.
- Canary catch rate: no canary planted (OI-15 still open). Escaped defects: none known (the gate hasn't run). Reopen rate 0.
- Cycle time: about 4.5 hours from plan to the last approval.
- Tokens per card (subagent totals, approximate): T-P1-1 380k + 230k r2 + 190k reviews; T-P1-2 270k + 140k r2 + 330k reviews (incl. security); T-P1-3 445k + 215k r2 + 200k reviews; T-P1-4 280k + 240k reviews (incl. security); T-P1-5 180k + 70k review; plan reviews 300k.

## Retro (short)
- Worked: the stub-first provider order (imaging `/preview` committed alone first) let T-P1-4 start while T-P1-2 was in review. The architect's plan review caught a softened control (files co-review) before launch. Reviewers ran real consumers (the backend client against imaging), which caught the T-P1-2 contract break that unit tests missed.
- Didn't: two cards' round 1s broke shared state or a consumer: a test that cleaned up a global registry, and imaging response codes added without checking the client's fixed enum. Round 2 edits in the shared backend tree looked like an unknown writer to the coordinator, because the wave file didn't name the active writer per path.
- Rules (lessons rows): tests of shared-infra registries use a unique, injected prefix and never touch global state. Imaging response changes are checked against `client.ts` and contract enums by running the real client. The wave log names the active writer when a round 2 starts in a shared tree.

## Hand-off (P1 tech lead, 2026-09-30): what the next tech lead does first
1. **Free :3000.** PID 91824 (`pnpm dev:api`, parent 56757, started about 6 h before the gate) holds it. Whoever started it stops it. If no one claims it, ask the owner; don't kill it blind. The API on :3142 (PID 91823) is the known unknown, so leave it alone.
2. **Gate:** `cd invai-infra && pnpm gate invai-backend invai-imaging invai-floor` (never `invai-infra`; OI-22). Disk: 6.4 GB free (OI-20); the gate needs room for the seed. If Docker or Valkey hangs, record it and stop.
3. **On pass:** look at /catalog/designs (40/40 thumbnails) and the floor QC result in Spanish, then push backend (5649c7c, b81a038, 7247b32, f5c0a68, c9fa1e5), imaging (2fc3806, f77e6e8, 26699d8), floor (ef1d926), and invai-docs (this wave's files plus 89f616e). On a failure, the card owner fixes it as round 3 (at most 2 rounds were used, so escalate if a card fails again).
4. **Then wave P2** (at most 5 cards, 3 agents), candidates in rank order for the PM: B-230 (losing orders units, verify), B-233 (preview robustness), B-223 + B-224 (raw English strings), Today actions jobId re-queue after 3 failures, B-231 (photo flags through contract and client), B-132 (architect: orpc patch or allow-list), invai-ui follow-ups (product-designer), B-227 (only if it recurs), B-232/B-234/B-235 (Low).
- Still paused: waves 24 and 25 (decision 0019). Fences: Track D out; OI-17 and OI-18 not approved.
