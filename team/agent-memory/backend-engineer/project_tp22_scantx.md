---
name: project_tp22_scantx
description: T-P2-2 — how to A/B a DB-transaction-contention hypothesis without git stash in a shared tree, and the floor-session auth chain for curling production.scan
metadata:
  type: project
---

T-P2-2 (B-233, gate root-cause §2) measured whether `renderDesignPreviews` holding a DB
transaction across `imaging.preview()` slowed `production.scan`. **Not reproduced** (round-1
report said "refuted"; reviewer r1 corrected it, round 2 reworded): API and worker are separate
processes with separate Postgres pools, and the render job only touches `design_files`, a table
`scan` never reads — 2 confirmed "idle in transaction" sessions during a 40-job burst didn't move
scan latency beyond jitter (p50 14-15ms either way vs 6ms idle). But `scan` was called directly on
the miss path (not over HTTP with a station token) and imaging was a 250ms Node stub, not real
imaging under load — too narrow a measurement to call the mechanism "refuted" outright. See
[[feedback_refuted_vs_not_reproduced]].

**Why:** the gate's own hypothesis was plausible on paper (transaction held during a slow HTTP
call) but wrong in practice for this codebase's process topology. Next suspect if this resurfaces:
Redis is actually shared (BullMQ + realtime pub/sub), unlike the Postgres pools.

**How to apply:** when a card's "prove or refute" needs an old-vs-new comparison and `git
stash`/`checkout --` is unavailable (another agent has uncommitted work in the same shared repo —
check `git status` first, every time), write a standalone script replicating the removed code path
byte-for-byte rather than touching tracked files. For `auth: "floor"` procedures (like
`production.scan`), a bare station token (`x-station-token`) gets 401 — you need a floor session
first via `POST /floor/login` (station token + a staff PIN from `seed-output.json`, plus
`x-contract-version` >= `invai-contracts/src/compat.ts`'s `CONTRACT_VERSION`), then
`Authorization: Bearer fs1....`.
