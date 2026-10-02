---
name: project-tp52-preview-cleanup
description: T-P5-2 preview cleanup/backfill — red-on-main proof trick without git stash; afterCommit runs after the driver's own commit
metadata:
  type: project
---

2026-10-01 T-P5-2: `.claude/hooks/guard-bash.py` blocks `git stash` outright, even with a
pathspec, in this shared tree. To prove a new test red on `origin/main` without it: back up your
own edited file (`cp x /tmp/x.bak`), overwrite it with `git show HEAD:path > path` (byte-identical
to main), run just the new tests (`-t "<name>"`), then restore from the backup and diff to
confirm. For a brand-new file the new test depends on, just `mv` it out to `/tmp` and back — no
git needed, since on main the import simply doesn't resolve.

**Why:** the only sanctioned options on the card were worktree-with-copied-test or "revert only
your own product edits"; stash is a blocked instruction-override risk in a multi-agent tree
(lessons waves 4, 8).
**How to apply:** any future "prove it was red on main" task in this repo.

Also: `afterCommit(tx, fn)` (`db/client.ts`) queues hooks that `scoped()` runs *after*
`database.transaction(...)` resolves — which is after the driver's own commit, not inside it. So
a cleanup/backfill registered via `afterCommit` is safe to call `withTenant` again (a fresh
transaction) and `withTenant(...)` as a whole only resolves once those hooks finish — in tests,
`await withTenant(...)` already reflects the afterCommit side effects, no extra tick/wait needed.
