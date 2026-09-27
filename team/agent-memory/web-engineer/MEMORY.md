# web-engineer memory

Seeded 2026-09-26 from `team/lessons.md` (T-16-3); every line below is a row there. Add your own entries under "Learned on cards": date, card, what you learned. No PII or secrets.

## Lessons that apply to you
- 2026-09-26 W8: Never `git stash`, `reset` or `checkout --` in a shared tree; compare in your own worktree at the base commit.
- 2026-09-26 W8: Don't push. Only the tech lead pushes, after the gate (a builder once pushed 44 ungated commits).
- 2026-09-25 W3: Shared files: stage only your hunks (`git add -p` / `git apply --cached`), check `git diff --cached`, then commit.
- 2026-09-24 W2: Kill only PIDs you started (`lsof -ti :<your port>`); never `pkill`/`killall`.
- 2026-09-25 W6/7: Never run `pnpm` inside a worktree; call `node_modules/.bin/*` directly. Never re-link shared `node_modules`.
- 2026-09-25 W3: Poll long jobs inside your turn with short sleeps; don't end your turn to wait.
- 2026-09-24 v1: Check the installed library API in `node_modules` before writing code (oRPC 1.15, drizzle 0.45, Zod 4, TS 7, Better Auth 1.7 are newer than training data).

## Learned on cards
- [Dev CSP needs build+preview](feedback_dev_csp_needs_build_preview.md) — `pnpm dev` CSP is hard-coded to :3000; use `vite build`+`preview` with `VITE_API_URL` and set `WEB_ORIGIN` on the API for a custom-port browser pass.
- [Never pkill](feedback_never_pkill.md) — always `lsof` for the PID then `kill <pid>`; never `pkill`/`killall`, even with a specific-looking filter.
- [T-17-4 assistant starters](project_t17_4_assistant_starters.md) — wave 17 tool-chip/starter-question pattern for the assistant screen; follow it for future analyst tools.
