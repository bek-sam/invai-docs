# Wave 4 — the floor app is complete

**Dates:** 2026-09-25. **Pushed:** yes, all four cards approved.

## What was built
- **T-4-1** Pack-complete, `wrong_style` and idempotent QC/bin, backend (backend-engineer/
  production): the server side of packing an order — a packer can't finish an order with
  units missing, and QC and bin assignment are both safe to retry.
- **T-4-2** Offline queue that never jams (floor-engineer): the tablet's local outbox
  (Dexie) keeps working, and keeps its scan order, when Wi-Fi drops.
- **T-4-3** Receiving station (floor-engineer): a new station type for checking in blank
  POs and vendor transfers on the floor tablet itself.
- **T-4-4** Pack station and floor polish (floor-engineer): UI and Spanish-copy cleanup
  across the floor flows built so far.

## Why
This is the floor half of module 05's core flow (gang sheet → floor scans → label) made
real end to end. A DTF shop's production floor is a tablet in a noisy room, often with
flaky Wi-Fi, run by staff who may read Spanish first. "Never jams" and "no English leaks"
are not nice-to-haves here — a jammed tablet or a mismatched scan stops physical shirts
from moving.

## What went wrong
- A builder ran `git stash` / `git stash pop` in the shared floor working tree just to
  measure its JS bundle size — `git stash` takes *every* agent's uncommitted changes in
  that tree, not just the stasher's own.
- The gate (`waves/4/gate.md`) passed clean on every automated check (contracts 31/31, ui
  20/20, imaging green, backend 447/447, web 55/55, floor 82/82, all builds, migration
  0016, API golden path 13/13, browser 15/15, floor 3/3) but flagged a real design
  limitation: two of the five smoke checks (the missing-unit block and hand-to-lead) are
  *unreachable through a pure click-through* because the Pack UI's own queue design hides
  the path — the gate verified those two directly at the API layer against the exact
  `production.packOrder` code instead of papering over the gap.
- One low-severity, non-blocking bug was filed as a fast-follow rather than a wave 4
  regression: `invai-ui` was missing the `station.receiving` translation key.

## What the team learned
- Never run `git stash`, `git checkout -- .` or `git reset` in a shared working tree —
  measure or experiment in your own worktree instead. This repeats (wave 8 hit the same
  mistake again) and is promoted into `respect-ownership`.
- When a UI's own design makes an acceptance check unreachable by clicking through it,
  the gate says so explicitly and proves the check a different way (direct API calls
  against the real service code) rather than skipping it or forcing an artificial path.
- A missing i18n key is exactly the kind of "small, precisely located" bug a gate should
  file and move on from, not block a push over.

## Files to look at
- `invai-backend/src/modules/production/service.ts` — idempotent pack-complete and QC (T-4-1).
- `invai-floor/src/outbox/` — the Dexie offline outbox (T-4-2).
- `invai-floor/src/routes/receiving*` — the new receiving station (T-4-3).
- `invai-floor/src/i18n/en.ts` + `es.ts` — floor copy, including the missed `station.receiving` key.
- `invai-docs/waves/4/gate.md` — the unreachable-smoke-check explanation and clean-pass evidence.
- `invai-docs/team/lessons.md` (2026-09-25, "Wave 4" row) — the `git stash` lesson.
