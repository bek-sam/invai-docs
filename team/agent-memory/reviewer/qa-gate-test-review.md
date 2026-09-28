---
name: qa-gate-test-review
description: Checks useful when reviewing QA-authored test commits made during an integration gate (as opposed to a feature card's own tests)
metadata:
  type: feedback
---

2026-09-28, wave 19 gate tests (`e2e/digest.spec.ts` selector fix, `market-scale.acceptance.test.ts`
AC28), both approved:

- When a gate fix changes a Playwright role/name selector to stop over-counting, don't just trust
  the commit message's story — read the component tree to confirm which elements are actually
  links vs buttons. Here `DigestInsightCard` renders `<AnyLink>` for normal actions but swaps to a
  `<RecommendationCard>` (all `<Button>`s) for `detector: "market"` insights, which is exactly why
  switching the selector from `getByRole("button", {name: /verb/})` to
  `getByRole("link", {name: /^verb\b/})` fixed the over-count without needing a `data-testid`.
- A selector fix that *narrows* the match (button→link) can still be checked for false negatives:
  grep the copy file for every action-text variant and check each starts with a verb in the
  regex. Found two (`seeWhatChanged`, `seeReprints`) that don't — pre-existing gap, not
  introduced by the fix, non-blocking since the current seed's top-3 never surfaces them, but
  worth naming so a future gate doesn't rediscover it from scratch.
- Opt-in `*_SCALE=1` acceptance tests in invai-backend (`digest/scale.test.ts`,
  `market/market-scale.acceptance.test.ts`) don't self-clean by design: `NODE_ENV=test` normally
  forces `invai_test`, but these are meant to be run with `TEST_DATABASE_URL`/
  `TEST_MIGRATION_DATABASE_URL` pointed at a throwaway DB that the operator drops afterward. Don't
  flag "no afterAll cleanup" here — check whether a precedent test in the same family already
  established the convention before treating missing cleanup as a finding.
- When a scale/acceptance test's docstring and the linked `qa-report.md` entry both plainly say
  which half of an AC they *don't* cover (here: AC28's 500ms-p95/≤20-row tool budget, left for a
  separate k6 run), that's a disclosed partial, not a blocking finding — grep the referenced spec
  line for the full AC text first so you can tell "disclosed gap" apart from "silently narrowed
  scope".

**Why:** these were the checks that actually mattered on a QA-test-only review (no feature code
in scope) where the risk is either a selector fix that trades one over-count for a different
under-count, or a scale test that quietly claims more AC coverage than it has.
**How to apply:** any round where the diff is QA's own `e2e/*.spec.ts` or `*.acceptance.test.ts`/
`*.scale.test.ts` file rather than a feature card's tests.
