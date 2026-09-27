---
name: feedback-scan-test-weakening-false-positive
description: scan-test-weakening.sh flags mock-gated production if-branches as "test-only branches" — check whether the condition is real data, not a false alarm
metadata:
  type: feedback
---

The independent-review scan script's "Test-only branches added to production code" section pattern-matches on
things like `if (mock && ...)` inside non-test files, but a branch gated on a real runtime field (a tool
output's `mock: boolean`, itself sourced from provider data) is normal production logic, not a test-only
shortcut.

**Why:** in T-18-4 round 2 it flagged `if (mock && !SAMPLE_LABEL.test(line)) parts.push(...)` inside
`assistant-tools.ts`'s `disclosure()` helper. `mock` there is the tool output's real mock flag, not a
test-fixture flag — legitimate, not blocking.

**How to apply:** when this section fires, trace the flagged variable back to its source before treating it as
a red flag. Only block when the condition checks something that could only be true in a test (a special-cased
id, an env var only tests set, a literal test string).
