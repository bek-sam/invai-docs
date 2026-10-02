---
name: seed-history-realism-review
description: Reviewing seed "history" cards - compare bulk-history volume/day against the live window, check date-relative windows (Q4 pick) across run dates
metadata:
  type: feedback
---

2026-09-30 T-A1 r1 (changes-required): bulk-inserted closed history ran at ~1.5 orders/day while the
live window (FULL_VOLUME 300+60 over 30 days) runs ~12/day, an 8x cliff at day -30 that every
basePeriod comparison would show as ~+700%. Also the Q4 year pick used histEnd month>=10, wrong for
runs Dec 2-Jan 1. ACs were met literally; the thresholds hid both.

**Why:** seed thresholds (>=30, >=1.5x) are easy to satisfy with planted rows; the realism lesson is about the shape.
**How to apply:** on any seed card, compute per-day volume of each generator from the code, run date-relative logic mentally for a December/January run, and check planted rows' timestamps against their items' transitions.
