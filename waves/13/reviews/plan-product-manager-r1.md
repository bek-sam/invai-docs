# Wave 13 plan review — product-manager, r1

Scope: contracts and quality. Read `team/agent-brief.md`, `waves/13/wave.md` + 5 cards,
`build/audit-2026-09-24.md` §A-INF (B-82/83/104) and §A-FE (no-UI procedure list), and the
`contract-deprecation` skill. Read-only on code; no DB writes, no commits outside `waves/13/**`.

## Verdict: plan is sound, scope needs one split

The wave's goal set (old tablets can't corrupt data, contract drift closed, E2E covers roles/Spanish/CI,
demo numbers credible) is coherent and each card maps to a real audit finding. The one product-scope risk:
**T-13-3 as written ("list the unused procedures") undersells the actual work.** Of the 13 no-UI
procedures, 12 are genuine missing UI for features that already have a backend and partial screen
(purchase order create/update, inventory count, station token revoke, ad spend, reprint queue, etc.) — that
is feature work, not cleanup, and doesn't fit inside a "drift cleanup" card sized for one architect. I
listed a verdict per procedure in `wave.md` and on the card. Recommend the tech lead either spins the
12 "use" procedures into their own backlog cards next wave, or explicitly descopes T-13-3 to just the
removal (`production.scanBatch`) plus its other four ACs (events, `Org.demoOwned`, attributes shape,
imaging contract test) this wave.

## T-13-1 (floor version handshake)
Design is now concrete in `wave.md` and the card: header name, error code (`CLIENT_TOO_OLD`, HTTP 426),
where the minimum version lives (backend env, not contracts — deliberate, so ops can hold the floor back
during the grace window without a contracts release), and a new outbox park reason (`stale_version`) that
separates "this old queued write's shape is now stale" from an ordinary rejection so a lead's alert is
actionable. This directly serves the "old floor tablets can't corrupt data" goal and is the one card I'd
keep on opus given the floor-correctness flag.

## T-13-4 (E2E coverage and CI)
The 15-minute CI budget is the one place the plan is optimistic without a note, and I flagged it as **not
realistic as scoped**: web/floor Playwright are pinned single-worker, E2E doesn't run in any of the three
CI workflows today (this is a from-zero add, not an extension), and the new spec count (14 web flows, 4
floor flows, 5 role specs, 2 Spanish passes, axe on top) will push the serial baseline well past a shared
15-minute ceiling summed across three independent jobs. I recommended reading the budget per-job and
turning on parallel workers for the state-independent additions (property tests, axe) while keeping
golden-path serial. This doesn't block the wave; it's a heads-up for whoever reviews T-13-4's definition
of done so "under 15 minutes" isn't silently redefined as "the sum of three jobs, one of which was already
over budget alone."

## T-13-5 (seed efficiency)
Confirmed the regression's cause (T-5-3's builder refactor swapped a lucky fixed-pairs layout for an
unsorted width-overflow shelf pack) and gave the fix (sort each sheet's chunk by width before packing).
Low-risk, isolated to two files, fully parallel-safe.

## Ownership / sequencing
Split into a 3-way parallel batch (T-13-1, T-13-4, T-13-5 — no file overlap, no shared `package.json`
touch) and a 2-card sequenced batch (T-13-3 then T-13-2, both touching `invai-contracts/package.json`'s
version field, which only one agent can hold at a time). Detail in `wave.md`.

## Changes made
- `wave.md`: added the ownership/sequencing table, the T-13-1 design, the T-13-3 verdict table, the
  T-13-4 budget check, the T-13-5 root-cause confirmation.
- `T-13-1.md`, `T-13-3.md`, `T-13-4.md`, `T-13-5.md`: added matching summaries + ownership blocks.
- This file and `plan-architect-r1.md`.
