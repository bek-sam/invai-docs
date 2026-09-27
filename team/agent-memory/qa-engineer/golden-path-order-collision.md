---
name: golden-path-order-collision
description: The API and browser golden-path suites import the same fixture CSV with fixed order numbers into the same seed company, so running both back-to-back without a reseed makes later steps skip/no-op — expected, not a bug.
metadata:
  type: project
---

`api-golden-path.spec.ts` and `golden-path.spec.ts` (invai-web) both import
`etsy-sold-order-items.csv` with fixed channel order ids (3310000001, 3310000002, ...) into the
same seeded company (`owner@desertbloom.test`). Import is idempotent by design (channel + channel
order id), so if the API suite runs first on a freshly seeded DB and finishes the whole flow
(map → approve proof → build sheet → vendor → receive → ship), the browser suite run right after
on the *same* DB sees "already imported/mapped/shipped" at each step and its tests print
`console.log` notes like "item already mapped on a previous run; skipping the drawer" instead of
exercising the UI path fresh.

**Why:** this is intended per the suites' own comments ("the browser one tolerates a re-run on the
same database", `qa-report.md` §4) — not a data-collision bug.

**How to apply:** when a gate runs both suites without a reseed in between (as `run-golden-path`
does — API suite first, then browser suite on the same fresh seed), expect these skip messages in
the browser suite's stdout and don't treat them as failures; the tests still assert the resulting
domain state regardless of which branch ran, per the golden-path spec's own comment at the top of
`clickIfShown`.
