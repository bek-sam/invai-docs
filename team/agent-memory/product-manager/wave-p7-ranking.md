---
name: wave-p7-ranking
description: 2026-10-01 P7 plan review found B-185..B-188 (Amazon DPP) as a missed agent-doable P2 compliance gap; B-132 stays architect-gated
metadata:
  type: project
---

P7 (2026-10-01) builds B-255, B-134, B-115, B-189 (plus B-262 folded into T-P7-3, B-261 deferred as Low).
Approved as plan-pm.md.

Doing a fuller sweep of `waves/backlog.md` ranges my [[wave-p6-ranking]] and [[wave-p5-ranking]] reviews
hadn't covered (lines 183-315: growth-opportunities, tech-lead reconciliation, analytics-v2 sections) found
**B-185, B-186, B-187, B-188** (Amazon DPP: account lockout, password history, 18-month non-PII retention
sweep, mandatory owner/admin MFA; filed wave 21 T-21-3) still open and agent-doable, with no SCR or outside
approval blocking the hardening work itself. They are `always-in-scope: compliance` under
`scope.md`'s own bullet (Amazon's data-protection rules) and no wave has touched them since wave 21.

**Why past reviews missed them:** my P5/P6 scope-review scans named specific line ranges to check
(P1/P2 tables, the full-codebase-audit P0/P1/P2 sections, the reconciliation table) but never the
later-appended sections past line ~218, where backlog rows get appended under stale/mismatched section
headers (e.g. DPP rows sit under a header literally titled "analytics v2"). **Lesson: when scanning
backlog.md for "what remains", check every row with status `open` via grep across the whole file, not just
named line ranges/headers** — the headers don't reliably describe what's under them this far into the doc.

Also re-confirmed **B-132** (assistant stream `net::ERR_ABORTED`, P2) is still open but intentionally
parked across P1/P2/P3/P6 rankings: needs the architect to pick patch-vs-allow-list first, cosmetic,
already mitigated. Not a new finding, just re-verified still true.

Recommended the tech lead fold B-185..B-188 into a P8 wave.
