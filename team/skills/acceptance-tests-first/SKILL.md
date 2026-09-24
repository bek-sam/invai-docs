---
name: acceptance-tests-first
description: Turn each InvAI task card's Given/When/Then criteria into failing tests before the build starts, at the lowest layer that proves them (Vitest on invai_test, API E2E, browser or floor Playwright), with some cases held back from the implementer. Use at wave step 3, when a card is planned, or when someone says "acceptance tests", "test first" or "red tests".
---

# Acceptance tests first

Before an engineer writes code, each acceptance criterion has a test that fails for the right reason, and the
tests the engineer can't see are ready to run at review.

## When to use
- Wave step 3 (QA), after the PM and architect reviewed the plan and before owners start building.
- A spec or card changed its criteria mid-wave.
- A bug card: the regression test comes first (`root-cause-bug`).

## Steps
1. **Read the card and spec.** List every criterion as Given/When/Then with a role, a starting state and an
   observable result. If one can't be tested, send it back to the PM (`write-spec`) before writing anything.
2. **Pick the lowest layer that proves each criterion** (research 12 §3.1):
   | Behavior | Layer | Where |
   |---|---|---|
   | pure logic: state machines, money, ship-by, matchers, SKU rules | Vitest unit | next to the module, `*.test.ts` |
   | service under a tenant, RLS, permissions, jobs, webhooks, S3 | Vitest on `invai_test` | `invai-backend/src/modules/<area>/<slug>.acceptance.test.ts` using `src/test/fixtures.ts` (`createCompany`, `createUser`, `createOrder`, `tenantContext` …) |
   | a whole API flow across modules | Playwright API | `invai-web/e2e/` (pattern: `api-golden-path.spec.ts`, helpers in `e2e/helpers/api.ts`) |
   | a screen flow | Playwright browser | `invai-web/e2e/` (helpers `e2e/helpers/ui.ts`) |
   | a floor flow (scan, PIN, block) | Playwright tablet | `invai-floor/e2e/` (pattern: `press.spec.ts`) |
   | nesting, rendering, file checks | pytest | `invai-imaging/tests/` |
   E2E only for flows. One criterion can need two layers (a service test plus one E2E step).
3. **Agree the file ownership.** The acceptance-test files (`e2e/**` and every `<slug>.acceptance.test.ts`,
   even inside a module folder the implementer owns) are QA-owned paths on the card and read-only for the
   implementer. Fixtures in `invai-backend/src/test/**` belong to backend-foundation: ask for a fixture change
   through a card, don't edit them. Ask the tech lead to list them on the card before you write them. Don't put acceptance
   tests inside the implementer's existing test files.
4. **Write the visible tests.** One `describe` per card, one `it`/`test` per criterion, named after it
   (`"AC2: replaying QC pass with the same clientScanId writes no transition"`). Always include:
   - the happy path on seed-style data (Desert Bloom Tees shapes; `scrub-pii-fixture` for anything from real
     data),
   - the refused cases: another tenant's id → `NOT_FOUND`; a role without the permission → `FORBIDDEN`,
   - replay: the same webhook, scan, job or label request twice → one effect,
   - the states the criterion names (cancelled after `on_sheet`, `on_hold`, `needs_mapping`, a reprint),
   - money in integer cents and sizes in unrounded inches in assertions.
5. **Hold some cases back.** For each card, write 1–3 extra cases the implementer doesn't see: the edge cases
   most likely to be missed (a second tenant, an off-by-one on a boundary, a replay after a crash, Spanish
   text overflow, a mock provider error). Keep them in
   `.claude/agent-memory/qa-engineer/held-back/T-<n>-<k>.md` (to be created; outside every repo) as
   ready-to-paste test code. They are added to the suite after the author reports done, before review.
6. **Prove they fail for the right reason.** Run them now:
   - backend: `pnpm test src/modules/<area>/<slug>.acceptance.test.ts`
   - E2E: per `run-golden-path` (fresh seed needed for the golden paths).
   Each must fail on a missing behavior (for example `NOT_IMPLEMENTED`, wrong state, missing row), not on a
   typo, an import error or a missing fixture. A test that passes already is either a wrong test or an
   already-met criterion: say which in your note.
7. **Commit the tests** in your owned paths only (`git -C <repo> add <files>`), marked so CI stays honest
   until the feature lands: use `it.fails(...)` (Vitest) or `test.fail(...)` (Playwright) with a comment
   `// T-<n>-<k>: remove .fails when the card lands`. Never `.skip`: a skipped test hides; a failing-expected
   test flips red the moment the behavior appears, which tells the implementer to remove the marker.
8. **Hand over.** Tell the implementer and the tech lead: the test files, how to run them, which criterion
   each covers. When the author reports done, add the held-back cases, run all of them, and give the results
   to the `reviewer`.

## Rules
- MUST write tests from the spec and card, not from the implementation or the implementer's plan.
- MUST keep every test deterministic: unique data per run, no `waitForTimeout`, frozen time for ship-by and
  periods, no dependence on other test files (research 12 §3.4–3.5).
- MUST NOT weaken or delete an acceptance test to match an implementation. A test you now think is wrong goes
  to the PM and tech lead with the reason.
- MUST NOT leave `.fails`/`test.fail` markers once the card is approved; the reviewer blocks on leftovers.
- The implementer MUST NOT edit acceptance-test files; they report disagreements instead
  (`respect-ownership`).

## Done when
- Every acceptance criterion maps to at least one test, listed in a table in your note (criterion → file →
  test name).
- Every test was run and fails for the stated reason (or is explained).
- Held-back cases exist for each card, stored outside the repos.
- Tests are committed in QA-owned paths with `.fails` markers and card ids, and the implementer knows how to
  run them.

## References
- `invai-docs/waves/templates/task-card.md` (criteria, verification)
- `invai-docs/research/12-security-quality-playbook.md` §3 (test pyramid, E2E and flaky-test rules)
- `invai-backend/src/test/fixtures.ts`, `invai-web/e2e/helpers/`, `invai-floor/e2e/helpers/api.ts`
- `.claude/agents/qa-engineer.md`; related: `write-spec`, `run-golden-path`, `root-cause-bug`,
  `independent-review`
