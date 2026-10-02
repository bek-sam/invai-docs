---
name: rule-change-stale-acceptance-assertion
description: When a PM-approved wording/behavior rule lands mid-wave, my own earlier acceptance test can assert the old rule unconditionally — check before assuming the implementer is wrong.
metadata:
  type: feedback
---

T-20-1 (wave 20): `market.acceptance.test.ts:627` (my wave-18 file) asserted
`r1.params.actByDate === season.actBy.date` unconditionally. The fixture's Halloween design gets a
hash-picked `peakMonth` of 9 or 10 (test already branches on this elsewhere with `=== 9 || === 10`
checks), and NOW was frozen at 2026-09-01. Once the wave-20 R1-timing wording rule landed (a peak
under way carries no act-by date), the test broke whenever the hash picked 9, since September was
already under way.

**Why:** the test was written before the wording rule existed and never anticipated a rule change
narrowing what R1 emits. The implementer correctly did not edit my file (`respect-ownership`) and
filed it instead of routing around it.

**How to apply:** before touching a "blocked by other owners" acceptance-test conflict, (1) confirm
the new rule is actually PM-approved (check `wave.md`/spec, not just the implementer's claim), (2)
reproduce the failure myself on a private DB, (3) if the test's own fixture already varies a value
across runs (hash-picked month, random id), branch the assertion on that value rather than assuming
a single expected outcome — don't just widen to `toBeUndefined() || toBe(x)`, since that would also
accept the old, wrong behavior. See [[gate-traps]] for other market/digest date-fixture traps.
