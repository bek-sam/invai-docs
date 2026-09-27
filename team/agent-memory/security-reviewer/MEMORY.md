# security-reviewer memory

Seeded 2026-09-26 from `team/lessons.md` (T-16-3); every line below is a row there. Add your own entries under "Learned on cards": date, card, what you learned. No PII or secrets.

## Lessons that apply to you
- 2026-09-26 W8: Never `git stash`, `reset` or `checkout --` in a shared tree; compare in your own worktree at the base commit.
- 2026-09-26 W8: Don't push. Only the tech lead pushes, after the gate (a builder once pushed 44 ungated commits).
- 2026-09-25 W3: Shared files: stage only your hunks (`git add -p` / `git apply --cached`), check `git diff --cached`, then commit.
- 2026-09-24 v1: Prove issues with failing tests; owners fix; the `reviewer` reviews the fix.
- 2026-09-24 rebuild: The first guard hook was bypassable (tag pushes, workflow runs, line continuations) and failed open; try those first.

## Learned on cards
- [Assistant tools Range span cap: S-33 fixed 2026-09-26](assistant_tools_range_cap.md) — new tools must use the `t()` wrapper to inherit it
- [ai.assistant.ask permission boundary](assistant_permission_boundary.md) — only owner/admin/office hold it, all already have finance.read; re-check if roles or tool data change
- [Assistant tool-line/shop-context pattern is sound](assistant_history_shop_context_pattern.md) — what to re-check when this pattern is extended
- [Guard/gate hook bypass patterns](guard_hook_bypass_patterns.md) — always try `npx`-style wrapper prefixes and `cmd | head -N` truncation when reviewing team hooks
