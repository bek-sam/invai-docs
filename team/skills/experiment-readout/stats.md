# Small-sample statistics for InvAI readouts

InvAI has 2–3 pilots now and maybe 10–20 shops at launch. Most readouts are counts, not statistics.

| Situation | Unit | Report | Don't |
|---|---|---|---|
| Pricing offer to pilots | Shop | "2 of 3 accepted Growth at $349" plus each objection | Percentages, p-values |
| Feature on for pilot A, off for B | Shop-week | Each shop's weekly metric side by side, before and after | Call it an A/B test; shops differ too much |
| Before/after on one shop | Day or week | Same weekdays, at least 2 weeks each side, and the 4-week trend before | Compare a Monday to a Friday; ignore a Q4 or TikTok spike |
| Floor change (e.g. new mismatch screen) | Scan or item, within a shop | Rate with counts and a 95% interval (Wilson for proportions); note the items are clustered by shop and presser | Pool shops as if every scan were independent |
| Trial or page test after launch (100+ units) | Visitor or trial | Difference with a 95% interval; sample size agreed before the start | Stop when it "looks significant" (peeking) |

## Wilson 95% interval for a proportion (x successes out of n)
```python
from math import sqrt
def wilson(x, n, z=1.96):
    if n == 0: return (None, None)
    p = x / n
    d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z * sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (c - h, c + h)
# wilson(12, 660) -> about (0.010, 0.032): a late rate of 1.8% could be anywhere from 1.0% to 3.2%
```

## Verdicts
- **Met:** the whole interval (or the count) clears the threshold, and the guardrail held.
- **Not met:** the whole interval falls short.
- **Inconclusive:** the interval spans the threshold, or confounders could explain the change. Say what would settle it.
