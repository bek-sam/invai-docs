# Wave 2 — money and accounts

**Dates:** 2026-09-24. **Pushed:** yes, all five cards approved.

## What was built
- **T-2-1** Stripe billing, backend (backend-engineer/billing): a shop can pay for a plan,
  and can't get a paid plan's features for free.
- **T-2-2** Billing UI and upgrade prompts (web-engineer): the screens that go with T-2-1.
- **T-2-3** Account security, backend (backend-foundation): email verification, password
  reset, optional MFA.
- **T-2-4** Account security, web (web-engineer): the screens for T-2-3.
- **T-2-5** Crash-safe labels, tracking and cancel (backend-engineer/shipping): buying a
  label can never double-charge, and a cancelled order never gets its tracking pushed or
  its postage wasted even if the process dies mid-call.

## Why
Wave 1 made it safe to add real keys. Wave 2 makes it safe to take real money — both the
shop's money (Stripe plans) and InvAI's own money (label purchases, which are postage
InvAI fronts and bills back). T-2-5 is the wave's clearest idempotency lesson: a label buy
that crashes between "charge the card" and "record the label" must never charge twice or
leave a ghost label.

## What went wrong
- A full disk (ENOSPC) hit mid-wave and stopped every agent and Docker at once. The
  cause: agents had been adding per-card test databases, worktrees and logs on top of an
  already-near-full disk.
- All 4 builders stopped mid-card at the same time when the account's shared usage limit
  hit — 4 Opus builders running at once used the whole session's budget in one go.
- A reviewer's `pnpm install`, run inside a review worktree, broke the shared
  `node_modules/@invai/contracts` symlink for every other agent, because pnpm relinks
  workspace dependencies relative to wherever it's run.
- A builder's `pkill` (used to restart its own API) was pattern-based and could have
  killed other agents' dev servers on a shared machine.
- A reviewer pushed `invai-docs` straight to `main` — review files and reports only, but
  the prompt had said "don't edit code," not "don't push."
- The gate's own E2E run (`waves/2/gate.md`) hit a real flake: after several manual
  kill/restart cycles of just the worker process against the same Valkey instance, step 9
  (shipping) needed a full stack restart, not another worker bounce, before it passed
  13/13.

## What the team learned
- Check `df -h /` before every wave (need more than 5 GB free); drop per-card test DBs and
  remove worktrees at every gate.
- Keep builders to 3 at once for long cards, and resume stopped agents with `SendMessage`
  instead of relaunching them from scratch — they keep their context.
- Review worktrees symlink `node_modules` from the shared repo and never run `pnpm
  install` inside one.
- Kill only PIDs you started yourself (save `$!`, or look up by the port you used);
  never `pkill`/`killall` on a shared machine.
- Every agent prompt now says "Don't push" explicitly — only the tech lead pushes, after
  the gate.
- After several manual process bounces against one shared Valkey instance, restart the
  whole `dev:all` tree once rather than bouncing pieces of it — the same rule
  `run-golden-path` already gave for after a reset, under-applied here until step 9 caught it.

## Files to look at
- `invai-backend/src/modules/billing/service.ts` and its Stripe webhook handling (T-2-1).
- `invai-backend/src/modules/shipping/service.ts` — the crash-safe label-buy path (T-2-5).
- `invai-web/src/routes/_app/billing*`, `account*` — the screens for T-2-2/T-2-4.
- `invai-docs/waves/2/gate.md` — the Valkey-restart flake and the full smoke-check table.
- `invai-docs/team/lessons.md` (2026-09-24, "Wave 2" rows) — disk, usage limit, symlink,
  `pkill`, and the push-guard lessons.
