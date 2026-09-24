# Lessons

Append-only. Add entries with the `log-lesson` playbook. A lesson that recurs is promoted into a playbook or role file, and into a hook or test when it can be checked mechanically. The "Enforced in" column says where the rule lives now.

| Date | Source | What happened | Cause | Rule | Enforced in |
|---|---|---|---|---|---|
| 2026-09-24 | v1 build | Agents ran out of the shared usage budget | Too many agents at once | Run 3–4 agents at once, not more | `CLAUDE.md`, `team/operating-system.md` |
| 2026-09-24 | v1 build | API died mid-request during E2E runs | `tsx watch` restarts on other agents' edits | Retry once; restart stale workers before E2E | `CLAUDE.md`, `run-golden-path` |
| 2026-09-24 | v1 build | Code written against the wrong library API | Libraries newer than training data | Check `node_modules` or official docs first | `read-before-change` |
| 2026-09-24 | v1 build | Gang sheets looked 51.7% efficient | Unrealistic seed art sizes | Keep the seed realistic (size mix per research 01) | `CLAUDE.md`, `scale-test` |
| 2026-09-24 | v1 build | Security fixes for B1/B2 shipped with no independent review | The reviewer fixed its own findings | Verifiers prove issues; owners fix; `reviewer` reviews | `team/operating-system.md`, role files |
| 2026-09-24 | Team rebuild | A playbook writer's reflow script rewrapped 26 files other agents were still writing | A bulk edit glob reached outside the agent's owned files | Bulk edits (sed, scripts, globs) touch only your own paths; list the files first | `respect-ownership` |
| 2026-09-24 | Team rebuild | The first guard hook could be bypassed (tag pushes, `gh workflow run`, line continuations) and failed open on bad input | Written as a denylist without an adversarial test pass | Every guard gets an adversarial test list and fails closed; the reviewer tries to bypass it | `guard-bash.py`, B-47 |
| 2026-09-24 | Wave 1 | A card's commit nearly included another agent's staged deletion (`seed/trademarks.ts`) | Several agents share one git index per repo; `git add <paths>` then a bare `git commit` commits everything staged | Commit with an explicit pathspec: `git commit -m ... -- <your paths>`, then check `git show --stat HEAD` | wave 1 builder prompts; promote to `respect-ownership` at retro |
| 2026-09-24 | Wave 1 | A test DB failed with "relation already exists" after another card regenerated its migration | drizzle picks which migrations to run by the journal `when` timestamp, not a content hash; regenerating changes it | After a migration is regenerated, drop and recreate your own test DB; don't regenerate a migration another card may already have applied — coordinate through the tech lead | wave prompts; promote to `zero-downtime-migration` at retro |
| 2026-09-24 | Wave 1 | A reviewer's `pnpm install` in a worktree broke the shared `node_modules/@invai/contracts` symlink | pnpm relinks workspace deps relative to the install location | Review worktrees symlink `node_modules` from the shared repo and never run `pnpm install` | wave 2 prompts and `wave.md` rules; promote to `independent-review` at retro |
