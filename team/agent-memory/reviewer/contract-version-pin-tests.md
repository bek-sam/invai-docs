---
name: contract-version-pin-tests
description: How to judge relaxed "at the end"/version-pin tests in invai-contracts on additive bumps, and how to mutation-test contract tests cheaply
metadata:
  type: feedback
---

On an additive contract bump, older waves' "last N enum names" and exact `CONTRACT_VERSION` pins must break. Relaxing them is legitimate only when the newest wave's test pins the full ordered enum and the exact version. Check that pin exists before accepting (2026-09-30 T-A2: analytics.test.ts pins all 19 tool names and 0.9.0).

**Why:** the change itself is not weakening; it becomes weakening only if no test still pins the exact values.
**How to apply:** use `git archive <sha> | tar -x` into the scratchpad, symlink node_modules, then perl-edit the permission, enum and range values and run vitest. BSD sed has no `0,/re/`, so use `perl -0pi`. When running a backend test file, use an empty Redis DB, then flush the bull:*:meta keys it leaves behind. See [[contract-review-checks]].
