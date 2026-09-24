---
name: root-cause-bug
description: Find the real cause of an InvAI bug across contracts, backend, web, floor, imaging, seed or environment - reproduce it, find the faulty layer, write a failing regression test at the lowest layer that catches it, then fix (owner) or file (anyone else). Use for "bug", "broken", "wrong number", "flaky", "works alone but not together", "regression", "500", "E2E failing".
---

# Root-cause a bug

A bug is reproduced, traced to the one layer that is wrong, pinned by a failing test at the lowest layer that can catch it, and fixed by that layer's owner, with nothing papered over.

## When to use
- Any failure: a failing test or E2E step, a wrong number on screen, a pilot report, a 500, a stuck job, a sheet that looks wrong.
- Everyone uses it. qa-engineer proves and files, never fixes product code; an owner fixes only inside its owned paths (`respect-ownership`).

## Steps
1. **Write the symptom down** in one line with evidence: the command, request, screenshot or log line, the expected vs actual value, the tenant (use seed tenants, never real shop data), and when it started (`git log` in each repo touched recently).
2. **Reproduce it on a clean stack** before theorizing:
   - stale processes are the top false alarm: `lsof -iTCP:3000-3199 -sTCP:LISTEN`, and any old `tsx src/worker` (a non-watch worker runs old code; `tsx watch` restarts the API when other agents edit files);
   - Docker/OrbStack hangs: `orb stop && orb start`, then `cd invai-infra/local && docker compose up -d`;
   - fresh data only where it's safe: `cd invai-backend && pnpm db:reset && pnpm db:migrate && pnpm db:seed` (imaging must be running for real art), never while other agents use the shared dev DB; prefer the test DB via a test;
   - golden path: `E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts` in `invai-web`, `pnpm e2e` in `invai-floor`.
   Can't reproduce? Record what you tried; don't guess a fix.
3. **Bisect by layer**, following the data from source to screen. Ask at each hop "is the value already wrong here?":
   1. input: CSV fixture or channel payload (`src/integrations/channels/**/fixtures`), normalizer output (`NormalizedOrder`);
   2. contract: schema or enum mismatch (`invai-contracts/src/schemas`), a new enum value an exhaustive switch doesn't know;
   3. backend service and DB: query the row directly as the app role inside a tenant (a quick Vitest against `invai_test` is faster than psql, which isn't installed here); check RLS (`withTenant` vs `withSystem`), the outbox row (`outbox_events.last_error`, `attempts`), the job (BullMQ failed set, worker log `job failed` with `queue`, `job`, `id`);
   4. imaging: call the endpoint directly with the same keys; check the 422 `detail`;
   5. frontend: the network response vs what renders (formatting in `src/lib/format.ts`, `Money`, i18n keys);
   6. seed or environment: unrealistic seed data (sizes once made sheets look 51.7% efficient), env flags (`env.mocks.*` in `src/env.ts`), a mock behaving differently from live.
4. **Name the faulty layer and the mechanism** in one or two sentences ("`updateExisting` applies an older Shopify payload over a newer address because it doesn't compare `updated_at`"). The first layer where the value is wrong is usually, but not always, the cause; check the layer above didn't pass something ambiguous.
5. **Write the failing test at the lowest layer that catches it** (research 12 §3.1):
   - pure function (money, ship-by, matcher, nesting, reducers) → unit test (Vitest or pytest);
   - DB or tenancy behavior → Vitest against `invai_test` with `src/test/fixtures.ts`;
   - contract shape → `invai-contracts` tests;
   - only a cross-repo flow → E2E (qa-engineer owns the suites).
   Run it and see it fail for the right reason before any fix.
6. **Fix or file.**
   - Your owned path: fix it; the test goes green; run the full checks for that repo.
   - Someone else's: file it to the owner through the tech lead with the one-line symptom, the reproduction, the faulty layer, the failing test (in your owned tests or as a patch in the report) and the evidence. Don't edit their files.
7. **Look for siblings.** Grep for the same pattern elsewhere (the same missing staleness check in another adapter, the same unmapped enum in the other app). List them in the report or file them.
8. **Learn once.** If the cause could recur, add a lesson (`log-lesson`) with where it is now enforced (a test, a lint rule, a playbook line). A High escaped defect gets a `postmortem`.

## Rules (MUST / MUST NOT)
- MUST reproduce before fixing, and see the regression test fail first.
- MUST NOT weaken a test to make it pass: no loosened assertions, `.skip`, `test.fixme` without an issue and owner, mocks of the unit under test, rewritten snapshots, or retries around a real failure. Environmental retries need a documented cause (research 12 §3.5).
- MUST NOT fix in a layer you don't own, or work around the bug in a layer above it (a frontend patch for a wrong backend number).
- MUST NOT paste real buyer data into tests or reports (`scrub-pii-fixture`).
- MUST stop any processes you started and leave the shared dev DB usable.

## Done when
- The report states symptom, reproduction, faulty layer, mechanism, and the regression test (file and name) that failed before and passes after.
- The fix is in the owner's path with the repo's full checks green, or the bug is filed to the owner with that evidence.
- Siblings were searched for, and a lesson was logged if the cause can recur.

## References
- `CLAUDE.md` (Environment, Lessons), `invai-docs/team/lessons.md`
- `invai-docs/build/qa-report.md`, `invai-docs/build/runbook.md`, `invai-docs/build/architecture-as-built.md`
- `invai-docs/research/12-security-quality-playbook.md` §3.1, §3.5
- Related: `run-golden-path`, `log-lesson`, `postmortem`, `respect-ownership`, `acceptance-tests-first`
