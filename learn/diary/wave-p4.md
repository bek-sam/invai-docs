# Wave P4 — true profit for reprinted orders, and the last Spanish screens

**Dates:** 2026-10-01.

## What was built
- **T-P4-1** Reprinted unit stays a sale: profit revenue, no re-import double unit
  (B-242) (backend-engineer/finance, orders, analytics, market) — the actual fix for the
  reprint profit bug module 10.3 covers in depth.
- **T-P4-2** Floor es: header pill fits (B-241); QC result and busy panel checked
  (floor-engineer).
- **T-P4-3** Web es: `/catalog/designs` checked and fixed; billing numbers confirmed
  (B-184) (web-engineer).
- **T-P4-4** Assistant/analyst queries count reprinted units (B-242 AI half) (ai-engineer)
  — the assistant's own numbers had to be fixed to match T-P4-1's corrected model.
- **T-P4-5** Acceptance fixtures use the real reprint model; market acceptance cache leak
  (B-221 rest) (qa-engineer).

## Why
Before this fix, a shirt that had to be re-pressed (a reprint) made the profit screen
show **$0 revenue and a false loss** for that order — the sale was still real, but the
accounting treated the reprint as if the original sale had never happened. See module
10.3 for the full story of how this was found and fixed; this entry covers the wave's
process side.

## What went wrong
- A test-file fix for this exact money bug had passed its review evidence while staying
  green with the *buggy* product code put back — the card had asked for "fixtures follow
  the real model," but not for proof that the test actually catches the old bug if it
  reappeared.
- A path grant written onto the card *during* the build (so the builder could touch a
  file outside its original owned paths) never reached the running agent — a running
  agent has no message channel, so a card edited after it starts is invisible to it.
- OrbStack hung for the **third time in two days**, this time for 8 minutes mid-QA-run
  and for roughly 3 hours stalling a web builder with uncommitted edits — Docker hangs
  are silent, and the tech lead only saw a quiet agent, with no obvious signal that the
  cause was infrastructure rather than the agent being stuck.

## What the team learned
- For every bug-fix or fixture card, both the author and the reviewer show the changed
  test fail on the pre-fix commit (with product files reverted in a worktree) — proof the
  test actually catches the bug, not just that it passes now. Promoted toward
  `independent-review` and `acceptance-tests-first`.
- Grants are given *before* a card starts, or handed to the path's actual owner as its
  own small task — never added to a running card's file expecting the agent to notice.
- When an agent's files and ports go quiet for 30 minutes, the tech lead now probes
  `docker ps` with a short timeout and restarts OrbStack if it's hung, before assuming
  the agent itself has stalled — this becomes a repeated, named step in
  `run-golden-path`.

## Files to look at
- `invai-backend/src/modules/finance/service.ts`, `src/modules/orders/service.ts` — the
  reprint-as-still-a-sale fix (T-P4-1).
- `invai-floor/src/i18n/es.ts` — header pill width fix (T-P4-2).
- `invai-web/src/routes/_app/catalog/designs.tsx` — es check and fix (T-P4-3).
- `invai-backend/src/modules/ai/analyst-queries.ts` — reprint-aware counts (T-P4-4).
- `invai-backend/src/modules/*/`.acceptance.test.ts` fixtures — T-P4-5.
- `invai-docs/learn/10-ai-team/03-real-incidents-and-what-we-learned.md` — the fuller
  reprint-bug story.
- `invai-docs/team/lessons.md` (2026-10-01, "wave P4" rows, three of them).
