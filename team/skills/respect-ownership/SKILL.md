---
name: respect-ownership
description: Stay inside your owned paths in InvAI's 8 repos. Check what you may edit, what to do when another owner's file blocks you (work around locally, report, never edit it), and how to commit only your own paths. Use before editing, before committing, and whenever a fix seems to need "just one line" in someone else's repo or module.
---

# Respect ownership

Every changed file is inside the card's owned paths, and anything outside them is reported to its owner
instead of edited.

## When to use
- Before the first edit on a card, and again before committing.
- A bug, missing export, wrong type or broken test sits in a path you don't own.
- A reviewer flagged "outside owned paths".

## Steps
1. **Know your fence.** Owned paths = the card's "Owned paths (edit)" list, which must sit inside your role's
   row in `invai-docs/team/operating-system.md` ("The team"). Everything else is read-only, including other
   modules in the same repo (for example `backend-engineer` on `modules/orders` does not edit
   `modules/production`, `src/db/**`, `src/lib/**` or `src/api/webhooks.ts`).
2. **Before editing a file, check it:** is the path matched by one of the card's owned globs? If not, don't
   edit it. There is no hook enforcing this yet (an owned-paths PreToolUse hook is to be created), so the
   check is yours.
3. **When blocked by someone else's file:**
   1. Confirm it is really theirs and really blocking (reproduce it; read the code with `read-before-change`).
   2. Work around it inside your paths if you can do so honestly: an adapter in your module, a local type
      narrowing, a test double in *your* test file for *their* unit (never a mock of your own unit under
      test).
   3. If you can't, stop that part and keep going on the rest.
   4. Report it. Put it in your final report under "Blocked by other owners" with: file:line, what is wrong,
      the failure you saw, the change you'd suggest, and the owner role. Tell the tech lead, who makes a card
      or adds it to the owner's current card.
   5. A security problem in someone else's code goes to `security-reviewer` at once. A High one also goes to
      `escalate-to-owner`.
4. **Shared generated files.**
   - Drizzle migrations: only through `pnpm db:generate --name <module>_<change>` for your module's schema,
     committed at once. If the journal collides, the later agent regenerates (`CLAUDE.md`). Never hand-edit an
     applied migration.
   - Contracts (`invai-contracts/**`) belong to the `architect`. Consumers ask; they don't edit.
   - Shared UI (`invai-ui/**`) belongs to the `product-designer`.
   - i18n catalogs: web strings are generated from `t("key", "Default")` calls in your own files (`pnpm i18n`
     in `invai-web`), so editing your own screen is enough.
5. **Check the diff before committing.** In each repo you touched:
   ```
   git -C <repo> status --short
   git -C <repo> diff --stat origin/main
   ```
   Every path listed must match your owned globs. Revert anything else you touched by accident
   (`git -C <repo> restore <path>` for your own stray edits only).
6. **Commit only your paths.** `git -C <repo> add <path> <path>` (never `git add -A` or `git add .` in a
   shared repo), then commit with the attribution line from your instructions. Pushing follows `CLAUDE.md`: in
   a wave the tech lead pushes after the integration gate; an agent working alone pushes its own finished,
   reviewed work.

## Rules
- Bulk edits (sed, scripts, globs) touch only your own paths. List the matched files before running them (lesson 2026-09-24).
- MUST NOT edit, format, or "fix a typo" in a path you don't own. Not even with Biome `--write` across the
  repo: run formatters on your own paths only (`pnpm exec biome check --write <your paths>`).
- MUST NOT copy another owner's code into your module to avoid asking. Report the gap.
- MUST NOT weaken, skip or delete another owner's test to make yours pass. That goes to `escalate-to-owner` if
  anyone proposes it.
- MUST NOT stage or commit other agents' work in progress, even if it is sitting in the same working tree.
- MUST NOT force-push, rewrite pushed history, change remotes, run `sst deploy` or change GitHub secrets.
  `.claude/hooks/guard-bash.py` blocks these; if it blocks you, the answer is `escalate-to-owner`, not a
  workaround.
- Reviewers and the tech lead are read-only on code. Verifiers (`reviewer`, `security-reviewer`, `qa-engineer`
  on others' features) prove the issue; the owner fixes it (`team/lessons.md`, 2026-09-24).

## Done when
- `git -C <repo> diff --stat origin/main` in every touched repo lists only paths inside the card's owned
  globs.
- Every blocker in someone else's path is in your report with file:line, failure, suggestion and owner.
- Nothing of anyone else's is staged or committed by you.

## References
- `invai-docs/team/operating-system.md` (ownership table, review rules)
- `CLAUDE.md` ("Repos, branches, ownership", migrations)
- `.claude/hooks/guard-bash.py`, wired in `.claude/settings.json`
- `invai-docs/team/lessons.md` (the B1/B2 self-review lesson)
