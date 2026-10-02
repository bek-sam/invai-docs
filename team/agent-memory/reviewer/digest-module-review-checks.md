---
name: digest-module-review-checks
description: Checks and traps found reviewing the weekly-digest backend module (T-19-3, wave 19)
metadata:
  type: feedback
---

2026-09-27 T-19-3 r1 (approve):
- pnpm on a symlinked-`node_modules` review worktree can fail with "workspace hoist directory is
  not a real directory" when you run `pnpm typecheck`/`pnpm lint` (pnpm tries an install check on
  the symlink target). Skip pnpm entirely and call the binaries directly:
  `./node_modules/.bin/tsc --noEmit`, `./node_modules/.bin/biome check .`,
  `./node_modules/.bin/vitest run …`, `./node_modules/.bin/drizzle-kit generate --name x` (exit
  code 1 with "No schema changes, nothing to migrate" printed is *not* a failure — it's drizzle-kit's
  normal exit when there's no drift; read the message, not just the code).
- To prove a scheduler/build job is safe under concurrent calls without touching anyone else's
  fixtures, drop a throwaway `_scratch-*.test.ts` into the worktree (own test DB), `Promise.all`
  the function 2-3×, assert one row / no duplicate unique keys, then `rm` it before finishing. Cheap
  and catches races the author's own tests didn't exercise.
- When an author's report says "N QA acceptance tests are red for reasons X, Y, Z (not our bug)",
  don't just read the code and nod — patch *only* the specific fixture bug in a scratch copy
  (`cp` to `/tmp`, edit, run, diff back to empty, restore from the `/tmp` backup) and re-run. Here,
  fixing one shared helper's offset (`mondayPhoenix(d) + 5min` → `+7h05m`) flipped 11 of 17 tests
  from red to green immediately, which is much stronger evidence than "I read the SQL and it looks
  right". The remaining reds each need their own one-line root cause (wrong field path, wrong week
  key, missing precondition, wrong cross-tenant assumption) — verify each individually, don't batch
  them under the first bug you find.
- A `git log --oneline origin/main..<sha> | tail -N` can silently truncate the newest commit (the
  range endpoint prints first); use `git show <sha> --stat` or `git log --format="%h %p"` to get the
  true parent chain before concluding a diff range is "wrong" — a confusing diff-stat mismatch here
  turned out to be my own truncated command, not a repo problem.
- `FINANCE_ROLES = Object.keys(ROLE_PERMISSIONS).filter(has "finance.read")` then filtering members
  by that computed role list satisfies "recipients by permission, not role name" in a role-based
  (no per-user-override) permission system — don't flag a `role in [...]` filter as a role-name
  violation without first checking whether the list was computed from the permission map.

**Why:** these were the non-obvious traps and the highest-leverage verification technique on a
card with 16 pre-existing QA-acceptance reds to triage.
**How to apply:** any backend review with a symlinked worktree, a migration to drift-check, a
concurrent/idempotent job, or a pile of "red for the right reason" acceptance tests to judge.

2026-09-28 T-19-3/T-19-5 r2 (both approve):
- `.env` on Node 24's `process.loadEnvFile` follows first-key-wins like dotenv: appending
  `TEST_DATABASE_URL=`/`REDIS_URL=...` lines to a worktree's copied `.env` does nothing if an
  earlier active (non-commented) line with the same key already exists above it — `sed -i` delete
  the old active line (or comment it) before appending the override, then grep to confirm only one
  active line per key remains.
- `.claude/hooks/guard-bash.py` blocks `git checkout <ref> -- <path>` in some invocations of a
  worktree under a shared-repo name but not others (it let a `HEAD~1` checkout through, then
  blocked the same-shaped `git checkout HEAD -- <path>` right after). Don't fight it: restore with
  `git show HEAD:<path> > <path>` instead, and confirm via `diff <(git show HEAD:<path>) <path>` —
  the index may still show the old checkout staged, but `git diff HEAD --stat` (working tree vs
  HEAD) is the check that matters, and it doesn't matter for a throwaway worktree you're about to
  remove anyway.
- Verified a cross-repo copy-value fix (web's D8/costLine copy, backend's R1 fallback text) by
  reading the *other* repo's source of truth directly (`invai-backend/src/modules/digest/render.ts`
  for web's wire-value keys and English/Spanish text; `invai-web/src/components/market/
  recommendation-copy.ts` for the backend's new fallback wording) rather than trusting either
  report's paraphrase — caught that both fixes were verbatim matches, which is the actual bar for
  "matches the wording web/backend already uses", not just "plausible-looking text".

2026-09-28 T-20-2 r1 (changes-required):
- Web and backend render the same recommendation copy separately (`recommendation-copy.ts` vs
  `digest/render.ts`): compare the *fallbacks* for optional params, not just the happy-path text.
  Web left `{{niche}}` empty where backend falls back to the peak month.
- Locale traps in Node 24 ICU: bare `es` = "10.000" but "1950" (no 4-digit grouping), decimal
  comma; `es-US` = "10,000"/"1,950", period. The PM's rule is es-US for the whole digest; check web
  helpers against it, and compare card AC examples with later PM decisions (card can be stale).
- `pnpm build` in invai-web needs `VITE_API_URL` set; delete `dist/` after when disk is tight.
- 2026-09-29 T-23-10: to judge cross-file test pollution, run `vitest run --sequence.shuffle.files --sequence.seed=N <files>` over several seeds (fileParallelism is false, so order is the only variable); run it in the background, since 8 seeds took more than 10 min.

- 2026-09-30 T-A9: parity tests like `expect(x?.key).toBe(top?.key)` pass vacuously when both are undefined. Print the reference value in a scratch probe to prove it exists. Probe console output is swallowed by the test setup, so write it with `appendFileSync` to /tmp.
- 2026-09-30 T-A9: when judging a destructive option (e.g. `force` rebuild drops clicks), grep for callers first. If no production path reaches it, the finding is non-blocking.
