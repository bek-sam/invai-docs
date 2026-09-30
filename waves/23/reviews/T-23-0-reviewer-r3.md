# Review of T-23-0 (round 3, reopen AC6; commit invai-backend d39a481 only)

- Reviewer: reviewer on claude-opus-5-5
- Author: backend-foundation on claude-sonnet-5
- Verdict: changes-required (first review of AC6; tech lead decides if the 2-round rule makes this `escalate`)

## Evidence I re-ran (scratch DB `invai_rev_t230_test`, Redis DB 12: DB 13 already held 139 foreign keys, left untouched)
| Command | Result |
|---|---|
| `pnpm typecheck`; `pnpm lint` | clean; `Checked 420 files … No fixes applied` |
| `pnpm test --reporter=dot src/test src/modules/shipping/jobs.test.ts src/modules/orders/state-machine.test.ts` | `Test Files 4 passed (4)`, `Tests 39 passed (39)` |
| Canary: insert company `canary-rev`, then `pnpm test src/test/db-safety.test.ts` | before 1 company / 5 plans / 471 marks; after 0 / 5 / 471: truncate ran, catalogs survive |
| tsx probe of `assertTestDatabase` (pure, no DB touched) | dev `…/invai` unpinned: REFUSED. Dev URL pinned as `TEST_MIGRATION_DATABASE_URL` or `TEST_DATABASE_URL`: **ALLOWED** |
| `scan-test-weakening.sh invai-backend d39a481~1` | no hits; assertions removed 0, added 9 |
| `git diff --stat d39a481~1 d39a481` | README.md, src/test/{db-safety.ts,db-safety.test.ts,fixtures.ts,global-setup.ts}: all owned |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| AC6 clean invai_test each run | yes | global-setup.ts:25-33: guard, then ensureDatabase, then migrate, then `truncateAll()` once per vitest run (globalSetup). Canary row removed; jobs.test.ts stuck-intent sweep green |
| Truncate can never hit dev DB `invai` | **no** | finding 1 |

## Blocking findings
1. `invai-backend/src/test/db-safety.ts:18-20` (and the claim in `README.md:64-65`): any URL that exactly matches `TEST_DATABASE_URL`/`TEST_MIGRATION_DATABASE_URL` is trusted whatever its database name, so the guard never catches the one misconfiguration it exists for. `env.ts:275-280` uses the pinned URL as-is. Scenario: an agent follows agent-brief.md:23 but pastes the dev URL (`TEST_MIGRATION_DATABASE_URL=postgres://invai:invai@localhost:5432/invai`, e.g. the `<db>` left as `invai`). `pnpm test` then passes the guard and `TRUNCATE … CASCADE`s every table in the shared dev DB, wiping the seed for every running agent. Before d39a481 the same mistake only added test rows. The README says the truncate "can never reach the dev database even if TEST_DATABASE_URL is … misconfigured", and that is false. Fix: always refuse when the database name equals the dev DB name (the raw `process.env.DATABASE_URL`/`MIGRATION_DATABASE_URL` path, or `invai`), even if pinned, or require "test" in the name with no pin exemption. Add a test "dev URL pinned via TEST_*_DATABASE_URL is refused".

## Checks
- [x] Only owned paths changed (`src/test/**`, README.md)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, none weakened (scan clean; the existing `truncateAll` is reused unchanged)
- [x] Tenancy/idempotency/money/i18n: n/a (test harness only). Truncate uses systemPool = MIGRATION_DATABASE_URL, and both URLs are guarded before any DB call
- [x] Decisions recorded: none needed

## Optional notes (not blocking)
- `/test/i` also matches names like `invai_latest` or `contest`. An anchored `(^|_)test(_|$)` would be tighter.
- I didn't reproduce the polluted-DB failure against base code (it needs 200+ stuck intents). The canary proves the truncate runs.
- README grew 12 lines, although the card says "one line on the test Redis DB". The text is accurate apart from finding 1.
