---
name: v1-review-staleness-pattern
description: How to re-verify v1-review.md's S-id table against code instead of trusting old statuses (T-21-3)
metadata:
  type: feedback
---

When asked to make v1-review.md's S-id table "current", grep the actual code for each "Open" row's claimed
gap instead of trusting the status column. T-21-3 (2026-09-28) turned up 3 stale "Open" rows that later
waves had silently closed as a side effect of unrelated feature cards: S-15 (email verification, fixed
wave 2/T-2-3), S-28 (webhook verify-before-enqueue), S-31 (SVG-never-inline, fixed T-12-5). One row (S-30)
was half-fixed but still marked flatly Open.

Why: the security log isn't automatically updated when a feature card fixes a gap as a byproduct — the fix
lands in that card's own report, not back in v1-review.md. A stale Open either causes duplicate work or
hides how many rows are genuinely still open.

How to apply: for each Open row, `grep -rl "S-<id>\b" invai-docs/waves/*/reports/*.md
invai-docs/waves/*/*.md` to find which card might have touched it, then read the current code at the cited
file:line. Also recompute the summary counts line at the bottom of the table — it drifts independently and
can undercount (it hadn't tracked S-33..S-37 being added, so it said 4 High when there were 6).
