---
name: ac-narrowing-check
description: Reviewer check when an AC was narrowed/deferred by a ruling — verify what the old code showed is not silently lost
metadata:
  type: feedback
---

2026-09-30 T-P2-4: the card's AC2 (after architect ruling 1) said the reason "stays as given", but the web change swapped `e.message` for badges, which dropped the transition reason entirely. The author reported it as "descoped", and wave.md said "shown as given".

**Why:** narrowed ACs drift between the card, the ruling and the log. A replaced render branch can remove information users relied on.

**How to apply:** compare the old and new render branches line by line, and query the dev DB (read-only) to see how often the dropped data really occurs. If the AC can't be met within the card's constraints, the verdict is escalate, not changes-required.
