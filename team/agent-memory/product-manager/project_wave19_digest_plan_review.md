---
name: wave19-digest-plan-review
description: Wave 19 (weekly digest) plan review outcome and the AC-coverage method used
metadata:
  type: project
---

Wave 19 tech-lead plan (T-19-1..5, weekly digest, item 17) was reviewed 2026-09-27 and approved with 2 minor
required changes: (1) no explicit acceptance criterion pins "no promotions/upsells" even though it's satisfied
by construction (templates are spec-copy-table only) — asked for a belt-and-suspenders assertion in T-19-3 or
QA's tests; (2) AC29 (scale test) is correctly deferred to QA's separate scale run per the spec's own text, but
the wave.md Integration gate checklist didn't list that run explicitly — asked for it to be added there.
Full table in `invai-docs/waves/19/reviews/plan-pm.md`.

**Why:** all 33 spec ACs must have a home (card AC, QA acceptance test, eval, or QA's separate scale run) before
a wave plan is approved — this is the standing check for every wave-plan review, not just wave 19.

**How to apply:** for future wave-plan reviews, build the AC-coverage table by grep'ing the spec's
`## Acceptance criteria (Given/When/Then)` section for the numbered list, then matching each number against
the `[AC...]` brackets in each task card's "Acceptance criteria" section. A scale/perf AC (like AC29) not
appearing in any card's brackets is not automatically a gap — check whether the spec itself names a separate
QA scale run as the intended home before flagging it.
