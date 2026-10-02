# Wave 6 — office web for inventory, production, profit and AI listings, plus demo safety

**Dates:** 2026-09-26. **Gated:** together with wave 7 (see wave 7's diary entry) — wave 6
has no standalone `gate.md`; it was still landing while wave 5's gate ran (see wave 5's
entry), so it was folded into the next combined gate instead of getting its own.

## What was built
- **T-6-1** Inventory UI (web-engineer + backend-engineer/inventory): make and edit
  purchase orders, count stock, set up supplier details — from the web app.
- **T-6-2** Production UI (web-engineer + architect for state, imaging for labels):
  in-house printing, reprints, bins and bin labels, all with a real UI instead of API-only.
- **T-6-3** Profit: ad spend, export, drill-down (web-engineer + backend-engineer/finance):
  the profit screen starts counting ad spend, not just order revenue and cost.
- **T-6-4** AI listings: copy, export, publish status, credits (ai-engineer + web-engineer):
  the first AI-generated listing copy feature, plus AI credit tracking so a shop can see
  what it's spending.
- **T-6-5** Demo workspaces can't spend real money (backend-foundation + integrations-
  engineer): a hard backend guarantee, reviewed by security alone, that a demo tenant can
  never place a real supplier order or buy a real label.

## Why
Waves 1 to 5 built the backend and the office's day-to-day screens. Wave 6 is where the
office gets *control* screens — inventory, production state, and the two features that
turn raw data into money decisions: profit (with ad spend) and AI-written listings. T-6-5
exists because AI listings and demo mode now touch things that cost real money if they
leak past a demo tenant's boundary.

## What went wrong
- `team/lessons.md` records two problems traced to this wave specifically:
  - The shared `node_modules/@invai/contracts` symlink kept getting rewritten to point at
    a review worktree instead of the real package, because `pnpm` had been run inside a
    worktree whose `node_modules` is itself a symlink. The fix: never run `pnpm` inside a
    worktree at all — use `node_modules/.bin/*` directly, and gates now check the symlink
    points back to `../../../invai-contracts`.
  - Grants the tech lead gave agents *only in chat messages*, not written into `wave.md`,
    caused two reviews to escalate later because the grant wasn't visible to the reviewer.
    From here on, every grant is written to the wave file in the same step it's given.
- As wave 5's gate flagged, wave 6's commits landed on `main` concurrently with wave 5's
  gate run, which is why wave 6 doesn't have its own clean standalone gate — it's folded
  into wave 7's "wave 6+7" combined evidence instead.

## What the team learned
- A worktree's `node_modules` is a pnpm symlink into the shared repo; running `pnpm`
  anywhere inside a worktree can silently relink shared packages for every other agent.
  This is now a standing rule for every review worktree.
- A grant that only exists as a sentence in a chat message doesn't survive into review —
  it has to be in the file the reviewer actually reads.

## Files to look at
- `invai-web/src/routes/_app/inventory/*` — purchase orders and stock counts (T-6-1).
- `invai-web/src/routes/_app/production/*` — in-house printing, reprints, bins (T-6-2).
- `invai-web/src/routes/_app/profit.tsx` and `invai-backend/src/modules/finance/` — ad
  spend in profit (T-6-3).
- `invai-backend/src/modules/ai/service.ts`, `invai-web/src/routes/_app/catalog/designs*`
  — AI listing copy and credits (T-6-4).
- `invai-backend/src/modules/tenancy/service.ts` (demo guard) and `src/integrations/` call
  sites that check it — T-6-5.
- `invai-docs/team/lessons.md` (2026-09-25, "Wave 6/7" rows).
