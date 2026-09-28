# backend-foundation memory

Seeded 2026-09-26 from `team/lessons.md` (T-16-3); every line below is a row there. Add your own entries under "Learned on cards": date, card, what you learned. No PII or secrets.

## Lessons that apply to you
- 2026-09-26 W8: Never `git stash`, `reset` or `checkout --` in a shared tree; compare in your own worktree at the base commit.
- 2026-09-26 W8: Don't push. Only the tech lead pushes, after the gate (a builder once pushed 44 ungated commits).
- 2026-09-25 W3: Shared files: stage only your hunks (`git add -p` / `git apply --cached`), check `git diff --cached`, then commit.
- 2026-09-24 W2: Kill only PIDs you started (`lsof -ti :<your port>`); never `pkill`/`killall`.
- 2026-09-25 W6/7: Never run `pnpm` inside a worktree; call `node_modules/.bin/*` directly. Never re-link shared `node_modules`.
- 2026-09-25 W3: Poll long jobs inside your turn with short sleeps; don't end your turn to wait.
- 2026-09-24 v1: Check the installed library API in `node_modules` before writing code (oRPC 1.15, drizzle 0.45, Zod 4, TS 7, Better Auth 1.7 are newer than training data).
- 2026-09-26 W7: A `db/schema` change ships with its generated migration in the same commit, and you run the backend tests, not only typecheck (68 tests broke once).
- 2026-09-24 W1: After a migration is regenerated, drop and recreate your own test DB (drizzle runs by journal timestamp).
- 2026-09-24 v1: Keep the seed realistic; seed sizes shape the product's numbers (the 51.7% sheet efficiency bug).

## Learned on cards
- 2026-09-27 T-18-1 (co-review, approve): see [wave18-t18-1-review.md](wave18-t18-1-review.md) — when co-reviewing an architect's ADR for a table another card will build, check the real committed schema file (it may already exist even while wave.md says "planned"); worktree-typecheck trick for pinning a backend commit against a specific contract version without touching the shared tree.
- 2026-09-27 T-19-1 (co-review, changes-required): an ADR/README that says "GET never mutates" and then describes a GET click-recording write in the same breath is a real inconsistency to flag, not nitpicking — a pinned auth-less-route doc that contradicts itself licenses two different implementations. The right fix is usually to narrow the absolute claim to the security-sensitive case (unsubscribe) and name the benign write (click record) as an intentional, idempotent exception, rather than deleting one side. Also confirmed: a company-keyed `checkRateLimit(bucket, companyId)` token bucket generalizes to an IP-keyed bucket for free (the second arg is just an opaque string) — no new limiter mechanism needed for auth-less routes.
- 2026-09-27 T-19-4 (email infra, B-133): see [wave19-t19-4-email-infra.md](wave19-t19-4-email-infra.md) — oRPC `call()` has an empty `path` unless passed (path-based middleware tests were never exercising `ai`); `ask` errors surface on iteration; strict `toEqual` on mailer skips; vendor-reachable procedures break authz's exact namespace list (security-reviewer's file).
- 2026-09-28 T-19-3 (co-review, 7-table migration, approve): `drizzle-kit generate --name <scratch>` in a disposable worktree against a DB migrated from zero is a stronger drift check than trusting a shared dev DB that had the migration pre-applied by another agent — "No schema changes, nothing to migrate" proves schema.ts and the committed SQL match exactly. `grep -rn "env.isTest" src/modules/*/jobs.ts` across all modules is the fast way to confirm a new `if (!env.isTest) scheduleXJobs()` line is the established self-registration convention, not a test-only shortcut the weakening scanner should flag.
