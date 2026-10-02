---
name: feedback_refuted_vs_not_reproduced
description: Say "not reproduced", not "refuted", when an AC0-style measurement only ran a narrower path/load than the real failure
metadata:
  type: feedback
---

When an AC0-style "prove or refute the hypothesis" task measures a *stand-in* for the real failing
path (a direct function call instead of the real HTTP/auth path, a fast Node stub instead of real
imaging under load, a replica script instead of the committed code), call the verdict "not
reproduced", never "refuted" or "confirmed". "Refuted" claims the mechanism can't be the cause
anywhere; a narrower measurement only shows it isn't the cause *in that narrower setup*.

**Why:** T-P2-2 round 1 measured `production.scan` by calling the service function directly (not
through the floor's real HTTP + station-token + PIN-session path) against a 250ms Node stub for
imaging (not real imaging under CPU load), and called the DB-transaction-contention hypothesis
"refuted". The reviewer (r1) and tech lead both flagged this as overstated — the gate's original
floor timeout is still unexplained, and a later card could wrongly drop this suspect based on a
test that never ran the path that actually timed out.

**How to apply:** before writing "refuted" in a report, check whether every real-world factor
(real caller, real auth, real downstream service under real load, the actual committed code
path) was in the measurement. If any of those was swapped for a faster/simpler stand-in, write
"not reproduced" and list the swapped factors as limits in the same paragraph. Reserve "refuted"
for a measurement that ran the real path end to end and still saw nothing. See
[[project_tp22_scantx]].
