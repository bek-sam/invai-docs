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
- 2026-09-27 T-18-1 (co-review, approve): [wave18-t18-1-review.md](wave18-t18-1-review.md) — check the real committed schema before trusting wave.md's "planned"; worktree-typecheck pins a commit against a contract version.
- 2026-09-27 T-19-1 (co-review, changes-required): [misc-safety-and-review-notes.md](misc-safety-and-review-notes.md) — self-contradicting "GET never mutates" docs are a real finding, not nitpicking.
- 2026-09-27 T-19-4 (email infra, B-133): [wave19-t19-4-email-infra.md](wave19-t19-4-email-infra.md) — oRPC `call()` empty path, `ask()` iteration errors, authz namespace list.
- 2026-09-29 T-20-5 (seed vs worker, B-106): [wave20-t20-5-seed-vs-worker.md](wave20-t20-5-seed-vs-worker.md) — seed counts shift at UTC midnight; pin a Redis DB per card.
- 2026-09-28 T-19-3 (co-review, 7-table migration, approve): [migration-review-notes.md](migration-review-notes.md) — drizzle-kit drift-check trick; migration lock_timeout/CONCURRENTLY precedents.
- 2026-09-29 T-22-1 (co-review, contracts 0.8.0, approve): [wave22-t22-1-review.md](wave22-t22-1-review.md) — gated-commit/revert-pair verification; enum-append consumer-break patterns.
- 2026-09-29 T-22-2 (composite tenant FKs, B-30): [wave22-t22-2-composite-fks.md](wave22-t22-2-composite-fks.md) — RLS-safe index conds, drizzle FK/unique-key ordering.
- 2026-09-29/30 T-22-2/T-A1/T-P1-1 (full-suite load flakes, seen 5×): [full-suite-flakes.md](full-suite-flakes.md) — always re-run a lone full-suite failure alone before calling it a regression.
- 2026-09-29 T-20-5 r2 (seed vs scheduled sweeps): [seed-ops-notes.md](seed-ops-notes.md) — scheduled job sweeps fire on registration; a shared insert loop can clobber a per-path decision.
- 2026-09-29/30 T-22-3/T-22-4/T-22-5/T-A3/T-A4 (migration co-reviews, approve): [migration-review-notes.md](migration-review-notes.md) — partial-unique-index pattern, snapshot-diff verification.
- 2026-09-29 T-23-0 r2/r3 (Redis/dev-DB guard, B-205): [redis-db-guard-edge-cases.md](redis-db-guard-edge-cases.md) — `Number()` parsing holes, identity-check-before-exemption.
- 2026-09-30 T-23-8 (digest seed, B-207): [wave23-t23-8-digest-seed.md](wave23-t23-8-digest-seed.md) — `recomputeProfit` must run sync at seed time; `seedOutput()`/Vite CSP port gotchas.
- 2026-09-30 T-23-10 (market-demand seed, B-207 follow-up): [wave23-t23-10-market-seed.md](wave23-t23-10-market-seed.md) — never run two `pnpm test` on the same DB/Redis at once.
- 2026-09-30 T-A1 (resume after OrbStack crash): [seed-ops-notes.md](seed-ops-notes.md) — mtime check for a stalled handoff; `dest_zone` seed-addition pattern.
- 2026-09-30 T-A1 r2 (verification-only resume): once the gate's full suite is green, a round-2 fix check needs only SELECT-only SQL, no reseed/full suite.
- 2026-09-30 T-P1-1 (per-run test DB/Redis, B-228): [test-infra-notes.md](test-infra-notes.md) — fake-timer/ioredis hang; globalSetup `provide`/`inject` channel.
- 2026-09-30 T-P1-1 r2 (review finding, B-228): [registry-test-isolation.md](registry-test-isolation.md) — a shared-registry unit test must never touch real keys, even for cleanup.
- 2026-09-30 T-P3-1 (B-236, bucketFor by intent): [misc-safety-and-review-notes.md](misc-safety-and-review-notes.md) — `bucketFor` priority-chain classification shortcut; PID-kill safety.
- 2026-10-01 T-P5-1 (resume, seed reprints, B-243): [wave-p5-seed-cleanup.md](wave-p5-seed-cleanup.md) — pin `REDIS_URL`/`SEED_OUTPUT_FILE` before any scratch reset/seed.
- 2026-10-01 T-P6-1 (safe db:reset/db:seed, B-219): [wave-p6-t1-safe-reset-seed.md](wave-p6-t1-safe-reset-seed.md) — guarding a script's auto-run `main()` call to make its pure checks unit-testable; duplicated-helper tradeoff vs read-only env.ts.
- 2026-10-01 T-P6-2 (SSE re-check, B-31): `createEvents({pingMs, probe})` makes /events testable; floor REST calls need `X-Contract-Version` (else 426); "Vite servers from exiting" after vitest is pre-existing noise.
- 2026-10-01 T-P6-2: `buildContext` swallows errors into anonymous; any revoke decision built on it needs an independent DB probe (ruling C1).
- 2026-10-01 T-P6-4 (seed determinism B-249, settled hand-over B-208): [wave-p6-t4-seed-determinism.md](wave-p6-t4-seed-determinism.md) — two-clock plan sort; Date-shift preload proof; DB snapshot for drain checks.
- 2026-10-01 T-P6-1 r2 (dual-URL seed guard, B-219): [wave-p6-t1-round2-dual-url-guard.md](wave-p6-t1-round2-dual-url-guard.md) — a multi-pool guard must check every pool's URL, not just one; give any live-check script that imports `seed/index.ts` its own hard timeout.
