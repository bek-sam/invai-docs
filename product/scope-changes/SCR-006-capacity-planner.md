# SCR-006: Capacity planner (press and printer load board)
Filed by: product-manager  Date: 2026-09-28  Type: add
Scope section affected: new capability next to scope.md#mvp-in items 1 and 14 (Today)

## Request
For each of the next 10 days, show units due to ship against press capacity (presses × pieces per hour, measured from scans) and printer capacity (sq ft per hour from the lower spec number, research 10 §8), minus a morning maintenance block. Flag red days early and suggest actions: pull sheets forward, add a shift, lengthen processing time on a channel (links to SCR-004). The projection uses open orders only; there is no demand-forecast model (fence).

## Why (evidence)
- Pressing is the bottleneck and operators are hard to hire: Impressions, 2026-09-22 and 2025-12-16 ([P], `research/16` §1.4).
- `research/03` pain #11 (peak season, TikTok spikes).
- Competitors: Printavo Power Scheduler; Pythias AI staffing forecast (claims) (research 16 §2).
- Shops confirmed: 0 pilots.

## Who it helps
Mid and large shops (owner, admin, office; floor leads).

## Cost and risk
- Effort: M, about 2–3 cards. Settings for presses and printers, a production stats service, a web board, and a Today alert.
- No spend.
- Risk: wrong capacity inputs give false alarms. Use measured throughput once 2 weeks of scans exist, and label estimates.

## If we don't
Shops find out a day is over capacity when orders are already late.

## Decision
Sent to owner (OI-17). The PM recommends **accept after** SCR-004 (they share the throughput data).
Reason: strong pain but medium confidence without pilot data.  Decided by: —  Date: —
