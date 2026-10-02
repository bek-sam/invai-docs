---
name: backlog-md-staleness
description: waves/backlog.md "open" status is often stale for items actually closed in waves 22/23/A1/A2/P1-P3; verify against the wave files before ranking or citing a row as open
metadata:
  type: project
---

`invai-docs/waves/backlog.md` rows are not reliably updated when an item is closed in a later wave,
especially for wave 22/23-era rows (e.g. B-25, B-30, B-139, B-164, B-183's siblings, B-223, B-236, B-237 all
showed stale "open"/wrong-wave text as of 2026-10-01 despite being done and pushed in waves 22, 23, P2 or
P3). `B-183`'s own row was updated correctly, so updates happen sometimes, not never — don't assume either
way.

**Why:** found doing the P4 plan review (`waves/P4/reviews/plan-pm.md`) and the P5 candidate ranking
(`product/backlog-ranking.md` 2026-10-01 entry): B-236/B-237 looked like fresh P5 candidates from their
backlog.md rows, but P3's wave.md showed they were T-P3-1/T-P3-2, already approved and pushed.

**How to apply:** before ranking or citing any `backlog.md` row as "open," especially one sourced from wave
22, 23, 23b, A1 or A2, grep the candidate's `B-###` id across `waves/*/wave.md` "Sources" lines and build
logs. A row only counts as genuinely open if no later wave's sources/build-log mentions it as done, or if it
explicitly names a remainder not yet covered (e.g. B-233: T-P2-2 did the transaction half, named the rest as
still backlog). Tell the tech lead to sweep `backlog.md` statuses periodically; don't just silently correct
rows yourself (not PM-owned to rewrite completed-item history without the tech lead's sign-off).

**Second lesson (2026-10-01, P7 review, see [[wave-p7-ranking]]):** when sweeping for "what agent-doable
P1/P2 items remain open," don't limit the scan to named line ranges or section headers — past line ~218 the
file appends rows under headers that no longer describe their content (e.g. B-185..B-188, Amazon DPP items,
sit under a header literally titled "analytics v2"). `grep -n "| open" waves/backlog.md` across the *whole*
file, then filter out Low/blocked/owner-pending ones, catches rows that a range-limited scan misses.
