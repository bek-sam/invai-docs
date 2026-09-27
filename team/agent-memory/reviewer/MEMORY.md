# reviewer memory

Seeded 2026-09-26 from `team/lessons.md` (T-16-3); every line below is a row there. Add your own entries under "Learned on cards": date, card, what you learned. No PII or secrets.

## Lessons that apply to you
- 2026-09-26 W8: Never `git stash`, `reset` or `checkout --` in a shared tree; compare in your own worktree at the base commit.
- 2026-09-26 W8: Don't push. Only the tech lead pushes, after the gate (a builder once pushed 44 ungated commits).
- 2026-09-25 W6/7: Never run `pnpm` inside a worktree; call `node_modules/.bin/*` directly. Never re-link shared `node_modules`.
- 2026-09-24 W1: Review worktrees symlink `node_modules` from the shared repo; never `pnpm install` there.
- 2026-09-24 v1: Verifiers report; owners fix. Never fix your own findings.
- 2026-09-26 W7: A `db/schema` diff without a migration in the same commit is a blocking finding.
- 2026-09-26 W6/7: A path edited outside the card needs a grant written in `wave.md`; if there is none, flag it.

## Learned on cards
