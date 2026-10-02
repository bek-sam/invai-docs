---
name: eval-cleanup-failure-probe
description: How to prove an eval route's tenant cleanup runs on failure without editing code (T-P1-3 r2)
metadata:
  type: feedback
---

2026-09-30 T-P1-3 r2: to prove the failure path of an eval route's `finally` cleanup, use a temporary script under `evals/` that passes a Proxy tenant that throws on property access to `runAssistantEvals`. Count `companies` in the dev DB before and after, then delete the script.

**Why:** reviewers must not edit code, but "deleted on failure" needs evidence beyond reading the code.
**How to apply:** for any cleanup-on-failure claim, inject the failure from outside through the function's inputs.
