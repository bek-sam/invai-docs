---
name: async-side-effect-visibility
description: When a card moves a side effect (email, push) from sync to a job, check that failed/unknown outcomes still reach the office; probe with a scratch test reading alerts + the entity's API detail
metadata:
  type: feedback
---

2026-09-29 T-22-5 r1 (changes-required): the vendor sheet email moved into a job with an at-most-once state machine (`unknown` after a crash, `failed` after 550). It was correct against double-sends, but nothing read the new table. The sync version used to return an error to the office; the async one lost the mail silently (the sheet still said "sent", no alert).
- Probe: copy the card's test fixtures into a scratch `zz-review.test.ts`, force the stale/failed state, run the job, then read the entity's `get` output and the `alerts` table. Print a one-line PROBE (use `--silent=false --reporter=verbose` to see the stdout).
- Also grep for readers of the new table outside the writer file.
- The fix precedent is `raiseAlert` from `today/service` (see `shipping/jobs.ts` `alertStuck`), reusing the closest alert kind.
- Mutation-test the "lock" half of lock+ON CONFLICT ACs: removing the lock often leaves the tests green.

**Why:** at-most-once is only acceptable when the "maybe lost" state is visible to a person.
**How to apply:** on any sync→async move of an outbound effect (email, tracking, label), check the failure-visibility path. See [[idempotency-concurrency-probe]].

2026-09-29 T-22-5 r2 (approve): fix verified by running the new tests against the prior commit's single file in a `git archive` scratch copy (3 red), and a perl-deleted advisory lock (3/3 red). Reusing an existing alert kind is acceptable as an interim if the sweep (`today/service.ts resolveStale` kinds list) doesn't auto-resolve it and the title carries the specifics; web shows only the English `a.title` in es.
