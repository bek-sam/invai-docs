---
name: sample-roundtrip-test-gap
description: A generic it.each round-trip over every enum code with sample values does not test the real call sites; mutate call-site params to prove it
metadata:
  type: feedback
---

2026-10-01 T-P5-4: the author covered "one test per alert kind" with `it.each(ALERT_MESSAGE_CODES)` that fed hand-built sample params into `raiseAlert`. It looked complete, but it never ran the call sites. Removing keys from generateAlerts params, or skipping the `AlertParams.safeParse` guard in toAlert, left every test green.

**Why:** if the test builds its own input, it only proves the storage layer, not the producer.

**How to apply:** when a card says "test per kind/code", delete one key at 2-3 real call sites, plus one guard branch, in your review worktree, then rerun. A surviving mutation in an owned file blocks under the AC.
