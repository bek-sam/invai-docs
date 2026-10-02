---
name: analytics-sort-tie-flake
description: Analytics services that sort cuts by value only flake on ties; run new analytics tests 4-6 times before approving
metadata:
  type: feedback
---

2026-09-30 T-A4: `operations-service.ts` sorted reprint cuts by cost/reprints with no key tiebreak and no SQL ORDER BY; the test expecting a fixed order of two tied rows failed 2 of 6 runs (first run passed).

**Why:** Postgres returns unordered rows in heap order, which varies between runs; a single green run hides it.

**How to apply:** for any service returning ranked rows (analytics, reports), loop the new test file 4-6 times (`for i in 1..6`, log to scratchpad, grep `Tests `) and check every sort has a deterministic tiebreak. See [[digest-module-review-checks]].

2026-09-30 T-A4 r2: proved the tie test by pairing the HEAD test with the pre-fix service in a scratch `git archive` (fails 2 of 3 runs). Also check the "other" sorts in sibling services (T-A3 channel/service groupings still sort by margin only). Never `cp` to `$R/..`: it wrote into the workspace root.
