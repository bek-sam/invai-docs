# Wave P5: Spanish alert and timeline text, realistic reprints in the demo, design preview loose ends

- Status: **planned** (2026-10-01). Planned from the hand-off at the end of `waves/P4/wave.md`.
- Goal (user outcome): under Spanish, Today's alert lines and the order timeline's reasons read in Spanish (today they show English sentences or nothing); the demo shop's reprints look like a real shop's (a few single shirts re-pressed inside bigger orders, not 44 orders reprinted end to end); a replaced design leaves no orphan preview files and order items mapped before their preview existed get one.
- Scope refs: always-in-scope (bug) for every card: B-224 + B-238 (Spanish leak on a daily screen, en/es is MVP item 5), B-243 (demo data shapes the product's numbers, CLAUDE.md seed-realism lesson; profit shows only all-reprint orders), B-233 rest (orphan objects and empty thumbnails in a shipped feature).
- Owner's scope for this wave: only agent-doable P1/P2 items (B-243, B-224 + B-238, B-233 rest, and any other P1/P2 the PM finds). Low (P3) items are skipped. If none remain after P5, the tech lead writes `waves/status-2026-10-01.md` instead of a hand-off.
- Fences: no deploys, no AWS, no outbound sends. Track D out. OI-17 and OI-18 are not approved. `invai-infra` is read-only and never pushed (OI-22). Waves 24 and 25 stay paused (decision 0019). No buyer PII. No rate limit or security control changed. Decision 0020 (reprint semantics) stands.
- Plan review: product-manager (scope; confirms no other agent-doable P1/P2 remains), architect (design: the contract shape for T-P5-3 and the cleanup rule in T-P5-2). The architect then builds T-P5-3 in the same run.

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| [T-P5-1](T-P5-1-seed-reprints.md) Seed reprints partial and ~3% of pressed items (B-243); seed previews through the catalog path (B-233 seed part) | backend-foundation (seed) | sonnet | reviewer (opus) | none (seed only) | planned |
| [T-P5-2](T-P5-2-preview-cleanup.md) Replaced design's old previews removed when unreferenced; late preview backfills order items (B-233 rest) | backend-engineer (catalog, orders/mapping) | sonnet | reviewer (opus) + security-reviewer (sonnet) | files | **approved r1** (backend 0aa67d8) |
| [T-P5-3](T-P5-3-contract-reason-params.md) Contract: alert `params`, timeline `reasonCode` + `reasonParams`, additive (B-224, B-238) | architect | opus | reviewer (sonnet) | contract | **approved r1** (contracts d6d038b) |
| [T-P5-4](T-P5-4-backend-reason-params.md) Backend fills alert params and timeline reason codes (B-224, B-238) | backend-engineer (today, orders/service timeline, alert callers in shipping, inventory, channels, vendors) | sonnet | reviewer (opus) + architect (sonnet) | none | planned (after T-P5-3 commits) |
| [T-P5-5](T-P5-5-web-reason-params.md) Web shows alert lines and timeline reasons from codes, en and es (B-224, B-238) | web-engineer | sonnet | reviewer (opus) + product-designer (sonnet) | ui | planned (after T-P5-3; live check after T-P5-4) |

Interfaces: T-P5-3 fixes the names (`Alert.params`, `TimelineEntry.reasonCode`, `TimelineEntry.reasonParams`, the code lists) before T-P5-4/5 start; both read the committed contract. All new fields optional, so the old backend and the cached floor/web keep working. No shared file between cards: T-P5-2 owns `orders/mapping.ts` (+ a new orders file), T-P5-4 owns `orders/service.ts`; T-P5-1 alone owns `src/db/seed/**`.

Order: plan reviews (PM + architect) → T-P5-3 (architect) and T-P5-1 → T-P5-2 → T-P5-4 → T-P5-5. Max 3 agents at once, reviewers included; max 2 heavy test runs.

## Slots and ports
- T-P5-1: scratch DB `invai_p5_seed` (drop at the end), imaging :8031, Valkey DB 13 (`REDIS_URL` pinned before any `db:reset`, B-219).
- T-P5-2: API :3150, Valkey DB 10. T-P5-4: API :3151, Valkey DB 9 (DBs 12 and 14 are used by orphan P4 APIs on :3141/:3143, see build log). T-P5-5: API :3152, web `pnpm build && pnpm preview --port 5190` with `VITE_API_URL=http://localhost:3152` (dev CSP fixed to :3000, B-212), Valkey DB 11.
- Gate slot (:3000, :5173, :5174, :8000) stays free. :3142 is held by an unknown API (PID 55461, since P4); left alone.

## Integration gate
- [ ] `pnpm gate invai-contracts invai-backend invai-floor invai-web` on a fresh seed (floor: contract consumer; imaging and ui unchanged)
- [ ] Tech lead looks at: Today alerts and an order timeline in es at 1440 and 390; reprint mix on the gate seed by SQL (share partial, share of pressed items, losing reprint orders)
- [ ] Push contracts, backend, web (floor only if it changed), docs. Never invai-infra (OI-22)

## Build log
- 2026-10-01 (P5 tech lead) Pre-wave: disk 12 GB free; docker healthy; all code repos clean at origin/main (contracts 6349ddf, backend 19a85c3, web 47acf01, floor b2cfd13, ui 2e3519d); gate ports free; :3142 held by PID 55461 (unknown, ~4 h old, left alone).
- 2026-10-01 Plan committed (docs 42e90a8). Started the PM scope review (sonnet) and the architect (opus: plan design review, then T-P5-3). Builders start after both plan verdicts.
- 2026-10-01 PM plan review: approve (`reviews/plan-pm.md`). Three more agent-doable P1/P2 items remain open: B-31 (floor SSE `?token=`, revoke doesn't close the stream), B-208 (sheet build races the post-seed outbox drain), B-219 (`db:reset` wipes queues in any Redis). P5 is at 5 cards, so they go to a P6 hand-off. Started T-P5-1 (backend-foundation, sonnet; AC5 waits for architect R3).
- 2026-10-01 Architect plan review: approve-with-changes (`reviews/plan-architect.md`, docs 35feb9d). R1: `Alert.messageCode` (new enum `ALERT_MESSAGE_CODES`, 14 codes, because `kind` is reused for several lines) + `Alert.params`; `TimelineEntry.reasonCode` (22) + `reasonParams`, derived at read time; consumers treat unknown codes as none. R2: delete old previews after commit, only `${cid}/preview/design/` keys referenced nowhere; late preview via `orders/preview-backfill.ts` called from `renderDesignPreviews`. R3: the seed keeps its direct `imaging.preview` call (can't see uncommitted rows; refuses placeholders), so T-P5-1 AC5 closes as a reasoned no-change.
- 2026-10-01 T-P5-3 built: contracts d6d038b (0.11.0; contracts 132 tests; backend, web, floor typecheck clean). Grant recorded after the fact: `invai-contracts/package.json` (version bump, architect's own repo). Started T-P5-2 (backend-engineer, sonnet) and the T-P5-3 reviewer (sonnet).
- 2026-10-01 07:30 T-P5-2 builder and T-P5-3 reviewer both died on the stream watchdog (no progress 600 s), no edits or files left. Docker and Valkey healthy. Found orphan P4 APIs (tsx watch respawned ~07:05): :3141 (Valkey 14), :3142, :3143 (Valkey 12), parents from P4; not this wave's, left alone; T-P5-2 moved to Valkey DB 10, T-P5-4 to DB 9. Relaunched both.
- 2026-10-01 T-P5-3 reviewer r1 (sonnet): approve (`reviews/T-P5-3-reviewer-r1.md`, docs 8a47cea): contracts 132/132, web/floor/backend typecheck clean, no existing enum touched, version-pin test move judged non-weakening. **T-P5-3 approved.** Started T-P5-4 (backend-engineer, sonnet). T-P5-5 waits for a slot.
- 2026-10-01 T-P5-2 built: backend 0aa67d8 (afterCommit cleanup per R2; `orders/preview-backfill.ts` `backfillItemPreviews` called in the preview write tx; catalog+mapping+backfill 25 tests; 2 of 3 new tests red with product files at main; live on :3150: unreferenced old preview deleted, referenced kept, presser@ 403). Coordinator note: full suite 1448 passed; lint red only in T-P5-4's uncommitted `today/service.test.ts` (must be clean before its commit). Reviewer (opus) started on T-P5-2; security-reviewer co-review queues.
- 2026-10-01 T-P5-2 reviewer r1 (opus): approve (`reviews/T-P5-2-reviewer-r1.md`, docs 65c9d43): 25 tests at 0aa67d8 in a worktree; delete and backfill tests red on 19a85c3; keep-when-referenced red with the reference check off. Notes (non-blocking): no test for the prefix check or the item_artwork/gang_sheets checks; backfill has no item-state filter, so a shipped item with no thumbnail can get a replaced design's new one (cosmetic; backlog). Started security-reviewer (sonnet) co-review.
- 2026-10-01 T-P5-4 built: backend cdeb3e3 (8 owned files; `reasonCodeFor` + 28-case table test; today tests for params, round trip over all 14 codes, re-raise updates params; full suite 1448 passed; live :3151 alerts carry messageCode/params, timeline shows on_sheet/sheet_received; presser@ 403). Tech lead ran biome on its 8 files: clean (the coordinator's lint note is resolved). Started T-P5-5 (web-engineer, sonnet). T-P5-4 reviews queue for slots.
- 2026-10-01 T-P5-1 report (in progress, docs 86a4b32): seed fix (order-scoped QC-fail flag; history reprints one item per multi-item order, target 160): 168 of 6162 pressed items = 2.73%, 97.6% partial, 2 reprint orders lose money, 0 at $0. AC5 closed per R3 (no change). Two scratch-env incidents, both disclosed by the builder: (1) a `db:reset` without `REDIS_URL` pinned obliterated the shared dev Redis DB 0 queues (B-219, second time); (2) a seed run without `SEED_OUTPUT_FILE` overwrote the shared `seed-output.json` with scratch ids. Both are dev-only and the gate's fresh reseed and restart repair them. Also found: the seed itself isn't run-to-run deterministic on origin/main (shipped 628/638/638) — new backlog row. Its full-suite run (PID 98318) is still going; commit pending.
- 2026-10-01 T-P5-2 security-reviewer r1 (sonnet): approve (`reviews/T-P5-2-security-reviewer-r1.md`, docs 6516b0a): two barriers before any delete (tenant read + `isCompanyKey` and prefix), `previewKey` only ever system-generated, backfill tenant-scoped; prefix regression test suggested as follow-up. **T-P5-2 approved** (reviewer + security). Started the T-P5-4 reviewer (opus).

## Metrics
(at close)

## Retro
(at close)
