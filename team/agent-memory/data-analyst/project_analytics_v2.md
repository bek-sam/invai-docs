---
name: project-analytics-v2
description: Analytics v2 plan (2026-09-28): where the spec, metric definitions, tested SQL, backlog rows B-168..B-183 and owner question OI-18 live, and what is gated
metadata:
  type: project
---

Owner asked 2026-09-28 for business analytics "to the 100% possible level"; I was woken before my pilot trigger to audit, define and spec (no product code).

- Spec `invai-docs/specs/business-analytics-v2.md` (draft for PM). Waves A1 (T-A1..A5 data/read services), A2 (T-A6..A10 web, assistant v6, digest D9–D13, Today actions), A3 gated (T-A11..A15).
- 20 definitions in `invai-docs/metrics/definitions/`, SQL in `invai-docs/metrics/sql/` (kept out of `invai-backend/scripts/**` because wave 20 T-20-5 owned that glob; move = B-182).
- Gated behind OI-18: goals, anomaly alerts, customer analytics (Amazon never; Etsy "no analytics" API clause needs counsel), cash view (= PM's B-152), scheduled report emails (OI-12/13/14).
- Overlaps with PM growth rows: B-153 = measured press time inside T-A4; B-146 shares digest D12.

**Why:** owner direction; 0 pilots have asked, so tracks A–C are SQL over stored data with no AI spend.
**How to apply:** check OI-18's answer and the PM's scope decision before touching wave A3; reuse these definitions rather than redefining. See [[seed-analytics-gaps]].
