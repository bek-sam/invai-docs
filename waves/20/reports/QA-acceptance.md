# Report: Wave 20 QA acceptance tests (T-20-1, T-20-2)
Author: qa-engineer on Sonnet 5

Resumed after the usage-limit stop. Both files were already on disk (uncommitted); I read them
against the brief, ran them, fixed the environment issues that blocked the E2E run, added the
missing T-20-2 AC2 coverage, and committed.

## Built
- Reviewed `date-copy.acceptance.test.ts` against T-20-1 AC1–AC5: all five covered (AC3 split into
  two `describe`s). No changes needed.
- Reviewed `digest-dates.spec.ts` against T-20-2 AC1–AC4: AC1, AC3, AC4 covered; **AC2 (points/
  unchanged on the glance grid) was missing**, so I added it (`invai-web/e2e/digest-dates.spec.ts`).
  It locates each StatCard by its label text (`Margin`/`On-time rate`) rather than forcing a
  specific before/after pair, since QA's web e2e path has no way to seed the digest pipeline
  directly — reads whatever the real week's delta is and asserts it's points or "unchanged", with
  no arrow icon when unchanged (a real `invai-ui` `StatCard` bug: `deltaDirection` defaults "up"
  whenever `delta` is a truthy string, so "unchanged" currently gets a green up-arrow).

## Acceptance criteria
| # | Covered? | Evidence |
|---|---|---|
| T-20-1 AC1 (no past peak) | Yes | `vitest` fail: past-peak item still returned (`true` not `false`) in both `digest.get.marketWatch` and `market.recommendations.list` |
| T-20-1 AC2 (peak under way wording) | Yes | fail: text is `"...before september."`, not `"season is on now"` |
| T-20-1 AC3 (points, not %) | Yes (2 tests) | fail: `"+26%"`/`"0%"` instead of `"+6.9 pts"`/`"unchanged"` |
| T-20-1 AC4 (mock asOf) | Yes | fail: `series.asOf` (1791158399999) is after frozen "now" (1790607600000) |
| T-20-1 AC5 (Today alert, no raw ISO) | Yes | fail: message contains `2026-09-26T15:00:00.000Z` |
| T-20-2 AC1 (Spanish heading) | Yes | fail: `"Semana del Mon, Sep 21"` |
| T-20-2 AC2 (points/unchanged, no arrow) — added this session | Yes (2 tests) | fail: `"+11.7%"` for both Margin and On-time rate, en and es |
| T-20-2 AC3 (refused page) | Yes (2 tests) | fail: raw `"Missing permission org.manage for digest.settings.get"` shown instead of the translated message |
| T-20-2 AC4 (thousands separator) | Yes (2 tests) | es fails (`"10,000"` shown, not `"10.000"`); en passes (already correct pre-fix, as expected) |

All 7 backend tests and 6 of 7 web tests fail now for the stated reason; the 7th (AC4 English) is
an expected pre-fix pass.

## Checks I ran
| Repo | Command | Result |
|---|---|---|
| invai-backend | `pnpm typecheck` | 1 pre-existing error, in T-20-3's uncommitted `shopify-live.acceptance.test.ts` (not mine); no errors in my file |
| invai-backend | `pnpm exec biome check src/modules/digest/date-copy.acceptance.test.ts` | clean |
| invai-backend | `pnpm exec vitest run src/modules/digest/date-copy.acceptance.test.ts` (TEST_DATABASE_URL/TEST_MIGRATION_DATABASE_URL → `invai_t20_qa`) | 7 failed / 7, all for the stated reasons (see above) |
| invai-web | `pnpm typecheck && pnpm lint && pnpm test && pnpm build` (VITE_API_URL=`:3000` for build) | all pass — 17 files/97 tests, build OK |
| invai-web | `pnpm exec playwright test e2e/digest-dates.spec.ts` (E2E_WEB_URL=`:4316`, E2E_API_URL=`:3116`) | 6 failed / 7, 1 passed (AC4-en), all for the stated reasons |

## Exercised for real
- Own API on `PORT=3116` against `invai_t20_qa_dev` (already-seeded dev copy). Own web: built to an
  isolated `dist-qa3116/` with `VITE_API_URL=http://localhost:3116` and served with
  `vite preview --outDir dist-qa3116 --port 4316` (per memory: never the shared `dist/`).
- **Environment fixes needed before the E2E run was valid** (both are environment/setup issues, not
  product bugs — logged to memory, not filed as bugs):
  1. `invai_t20_qa_dev` had no `invai_app` grants on `users` (and presumably every other table) —
     `sign-in/email` 500'd with `42501 permission denied for table users`. Reapplied the three
     GRANT statements from `invai-backend/drizzle/0001_grants_extensions.sql` directly.
  2. My API (port 3116) rejected the login with `INVALID_ORIGIN` (403) because `.env`'s
     `WEB_ORIGIN=http://localhost:5173` didn't match my web preview's `:4316`. Restarted the API
     with `WEB_ORIGIN=http://localhost:4316` and `BETTER_AUTH_URL=http://localhost:3116`.
  After both fixes, `curl .../sign-in/email` returned 200 with a session cookie, and the suite ran
  cleanly (no more login timeouts).

## Decisions
- Added T-20-2 AC2 web coverage this session (not present in the pre-stop file) rather than leaving
  it untested going into the build — it's a real, distinct bug (`invai-ui`'s `StatCard` arrow
  default) that the card explicitly calls out ("no arrow and a neutral color").

## Known gaps and follow-ups
- None for the acceptance suite itself. The dev-copy-DB-grants issue may affect other agents'
  `createdb -T invai` copies this wave (T-20-1's `invai_t20_1_dev`, T-20-2's own `invai_t20_2`) —
  worth a heads-up to the tech lead so those owners check login before relying on their copy.

## Blocked by other owners
- None.

## Processes and data
- Started and stopped (recorded PIDs): API on `:3116` — first instance 81142/81150/81157 (stopped,
  missing `WEB_ORIGIN`), second instance 82354/82362/82369 (stopped after the run). Web preview on
  `:4316` — 81425/81434 (stopped). `dist-qa3116/` removed (untracked, not gitignored — confirmed
  clean `git status` after removal).
- `invai_t20_qa` and `invai_t20_qa_dev` dropped; Redis DB 15 flushed. Shared dev DB (`invai`, port
  3000 API pid 68649) untouched.

## Commits
- `invai-backend` `b307de0`: `src/modules/digest/date-copy.acceptance.test.ts`
- `invai-web` `f5af662`: `e2e/digest-dates.spec.ts`
- Not pushed (tech lead pushes after the gate).
