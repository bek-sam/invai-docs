---
name: parallel-wave-cards-not-settled-fact
description: Don't let a card cite a sibling card's in-progress, unreviewed behavior as an established fact
metadata:
  type: feedback
---

When reviewing a card in InvAI, check whether it states as fact the behavior of another card running in the same wave that hasn't been reviewed/approved yet (found in T-16-3 round 1, 2026-09-26: seeded memory lines described T-16-2's guard-hook behavior as a settled "lesson" while T-16-2 was still awaiting its own adversarial review in the same wave).

**Why:** a sibling card can change behavior after review; anything that presents it as already-true, dated evidence becomes silently stale with no mechanism to correct it, since it was never logged as an actual lesson/decision.

**How to apply:** cross-check any such claim against `team/lessons.md` (or the relevant decision/spec) rather than trusting the diff's own narrative. Flag as a blocking finding if the card treats unreviewed sibling-card behavior as settled truth in something persistent (docs, seeded memory, changelogs).
