# Review of T-P6-1 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: backend-foundation on Sonnet 5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `tsc --noEmit` / `biome check .` (worktree /tmp/p6-1-wt at fb424fe) | exit 0 / 460 files, no fixes |
| `vitest run src/db/reset.test.ts src/db/seed --reporter=dot` | 6 files, 19 passed |
| Same 2 test files with both `if (database === "invai") return` mutated to `if (database) return` | 5 failed (3 reset refusal, 2 seed refusal), 8 passed: refusal tests are red without the guards |
| `tsx src/db/reset.ts` on scratch `invai_p6_r1`, REDIS_URL no path, then `/0` | exit 1, card's message; `sentinel` table still there; Redis DB 0 dbsize 5721 before/after |
| Same with `/13` | exit 0, schema recreated, queues obliterated in /13; DB 0 still 5721 |
| `tsx src/db/seed/index.ts` on scratch, SEED_OUTPUT_FILE unset | exit 1, refusal names the variable; 0 public tables created; `seed-output.json` mtime unchanged (08:52) |
| Same with SEED_OUTPUT_FILE=/tmp/p6-1-r.json | guard passes, fails later on unmigrated schema (expected) |
| Seed via relative path from symlinked `/tmp/...` and from `/private/tmp/...` | main() ran both ways (refusal printed): the argv[1] main-guard keeps `pnpm db:seed` / run-e2e.sh `tsx src/db/seed/index.ts` working |
| R3 probe: tsx script, DATABASE_URL=…/invai_p6_r1, MIGRATION_DATABASE_URL=…/invai, no SEED_OUTPUT_FILE, calling `assertSafeToSeed` exactly as main() does | `guard PASSED` (R3 requires a refusal) |
| `scan-test-weakening.sh invai-backend fb424fe~1` | no hits |
Cleanup: scratch DB dropped, worktree removed, /tmp/p6-1-r.json never created; shared `invai` and `seed-output.json` untouched.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `invai` returns early before any check (reset.ts:27, seed/index.ts:68); CI/gate envs all name `invai` |
| 2 | yes | live refusal above, before Postgres/Redis |
| 3 | yes | live /13 reset above |
| 4 | partly | refuses on a non-`invai` MIGRATION_DATABASE_URL; see finding 1 |
| 5 | **no** | reset half met (guard only in the main block, reset.ts:122; `ensureDatabase` untouched). Seed half not met: the seed guard checks **only `MIGRATION_DATABASE_URL`, not `DATABASE_URL`** |
| 6 | yes | pure functions, allow+refuse unit tests, red with guards removed (above) |

## Blocking findings
1. `invai-backend/src/db/seed/index.ts:63-75,86` — `assertSafeToSeed(migrationDatabaseUrl, seedOutputFile)` takes no `DATABASE_URL`, and main() passes only `env.MIGRATION_DATABASE_URL`. R3 (AC5) says refuse unless **both** URLs point at `invai` or SEED_OUTPUT_FILE is set. The seed writes through both pools: `systemDb` (MIGRATION_DATABASE_URL, client.ts:12) and `auth`/`signUp` (`db`, DATABASE_URL, client.ts:8). Failure: an agent exports only `DATABASE_URL=…/invai_scratch` and keeps `.env`'s `MIGRATION_DATABASE_URL=…/invai`. The guard passes (proven above). If the shared `invai` has just been reset, companies go into `invai`, users into the scratch DB, and the shared `seed-output.json` is overwritten. Fix: take both URLs, refuse when either names a database other than `invai` and SEED_OUTPUT_FILE is blank, and add a unit test for each mixed case (red without the fix).

## Checks
- [x] Only owned paths changed: README.md, src/db/reset.ts, reset.test.ts, seed/index.ts, seed/safe-seed.test.ts
- [x] Nothing outside scope. The seed main-guard is a structural change beyond "only the guard", but AC6 needs it, and I proved it still runs main()
- [x] Tests exercise the behavior, none weakened (scan: no hits)
- [x] Tenancy/idempotency/money/i18n: n/a (dev tooling, no schema, no UI)
- [x] Decisions: none needed

## Optional notes (not blocking)
- The report's AC table has 5 rows and skips the card's AC5 (R3). Round 2 should list it.
- Importing the seed module registers the market schedulers in Redis (`market.jobs` log line on the refusal path). This predates the card and AC4 only says "before any insert", but the seed still touches Redis before it refuses.
