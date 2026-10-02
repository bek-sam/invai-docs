---
name: wave-p5-ranking
description: 2026-10-01 P5 scope review found 3 more open agent-doable P1/P2 items beyond B-243/B-224+B-238/B-233; ranked for P6
metadata:
  type: project
---

P5 plan review (approved) also had to answer: are there other agent-doable P1/P2 backlog items open besides
the three P5 already takes? Checked `backlog.md` "P1"/"P2 and later" sections plus every Medium/High-tagged
row against the actual wave files (many "open (P2 sweep)" rows are stale — see [[backlog-md-staleness]]).

Found three real open items, ranked for a P6 hand-off:
1. **B-31** — floor SSE still sends `?token=` in the URL plus the Authorization header, and a revoked
   station token doesn't close the open stream (`invai-floor/src/realtime/sse.ts:88`). Security/pilot-safety
   gap on the "lost or stolen tablet" revoke flow. Open since wave 5; skipped by three P2-sweep waves
   (22, 23, 23b) without ever being picked up.
2. **B-208** — `production.batches.build` can run while the post-seed outbox drain is still filling the
   item pool, so a sheet can ship under 80% film use (reproduced once in CI, 0.7951). Real race in the
   gang-sheet wedge, not just a flaky gate.
3. **B-219** — `pnpm db:reset` wipes BullMQ queues in whatever `REDIS_URL` it resolves to, even for a
   scratch DB; already caused one real incident (wiped shared dev DB 0 queues, 2026-09-29).

**Why they were missed before:** none are in the "Added 2026-09-24/28" sections the tech lead reconciles
most often; B-31 predates the severity-tag convention entirely, and B-208/B-219 are tagged Medium but sit
far down the "Added 2026-09-28" reconciliation list where severity isn't the thing scanned for.

**How to apply:** when ranking after P5, start from these three rather than re-deriving them; re-check
wave files for B-31 specifically since it has been skipped repeatedly (confirm it's still really open, not
just still listed).
