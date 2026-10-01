# Plan review (scope): wave P5. Product-manager

Reviewer: product-manager. Scope: scope refs, fences, and whether other agent-doable P1/P2 backlog items
remain beyond B-243, B-224+B-238, B-233 rest.

**Verdict: approve.**

## Scope refs
All five cards correctly claim `always-in-scope: bug`. T-P5-1 (seed realism for reprints) matches
CLAUDE.md's seed-realism lesson, same ground as the P4 review accepted for B-242/B-243. T-P5-2 (orphan
preview cleanup, late-preview backfill) is a bug in a shipped feature (catalog), continuing T-P1-4/T-P2-2.
T-P5-3/4/5 (alert params, timeline reason codes, en/es) extend MVP item 5 (en/es) to Today and the order
drawer, same basis the P4 review used for B-241/B-184. Nothing builds past `scope.md`; no
scope-change-request needed.

## Fences
No card touches `invai-infra`, Track D, OI-17/18 items, or waves 24/25. No deploy, AWS or outbound send in
any card. Contract change (T-P5-3) is additive only, as required. Fences hold.

## Other open agent-doable P1/P2 items (beyond the three named)
Checked `backlog.md` "P1" (lines 29-53) and "P2 and later" (55-73), plus every row tagged Medium/High
anywhere in the file, against the wave files (not the row text, which is stale in places — e.g. B-32 and
B-35 show "open (P2 sweep)" but are done: wave 22 T-22-4 and wave 23 T-23-2 built bin locations, QC fail
reasons, transfer-age warning and maintenance block; B-204 confirms the code exists, only the seed data is
thin. B-37's indexes half is done (wave 22 T-22-2); its fan-out half and B-34/B-38 are already in wave 25.
B-41's display half is covered by the A1/A2 operations screen's `filmUsePct`. B-49 folded into analytics A1
per the wave 22 note.

**Three remain open, agent-doable, not excluded by any fence:**

1. **B-31** (P2 table) — Floor SSE still authenticates with `?token=` in the URL (`invai-floor/src/realtime/
   sse.ts:88`) alongside the Authorization header, and a revoked station token doesn't close the open
   stream (noted since wave 5, never actually picked up in waves 22/23/23b despite three P2-sweep passes).
   Security/ops gap on the "lost or stolen tablet" revoke flow pilots will use. Risk flag: auth.
2. **B-208** (Medium) — `production.batches.build` can run while the post-seed outbox drain is still
   filling the item pool, so a sheet can ship under 80% film use (reproduced once in CI). This is a real
   race in the gang-sheet wedge's correctness, not just a test flake.
3. **B-219** (Medium) — `pnpm db:reset` wipes BullMQ queues in whatever Redis `REDIS_URL` resolves to,
   even when resetting a scratch DB; already caused one real incident (wiped shared dev DB 0 queues,
   2026-09-29). Tooling/data-safety risk for the team, not shop-facing.

## Ranked for a P6 hand-off
1. B-31 — security/pilot-safety (revoke must actually cut access), skipped three times already.
2. B-208 — core-wedge correctness (gang-sheet film efficiency), flagged as a flaky-gate risk.
3. B-219 — internal tooling data-safety, lower shop impact but a repeat-incident risk.

Recommend the tech lead plan a P6 wave from this list rather than writing a status-only file at P5's close.
