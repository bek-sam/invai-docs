# Draft scope-change request: analytics v2, gated items (for the PM to file as the next SCR)

Filed by: data-analyst (draft; the PM owns `product/scope-changes/` and files it)  Date: 2026-09-28  Type: add
Scope section affected: scope.md#mvp-in items 8, 14, 17; `decisions/0006-v1-cuts.md` (not reopened)
Spec: `specs/business-analytics-v2.md` (Track D). Owner-inbox: OI-18.

## Request
Add five analytics capabilities that are outside current scope:
1. **Goals and targets**: the shop sets monthly targets (net profit, on-time rate, reprint rate, film use); Today and the digest show pace.
2. **Anomaly alerts**: robust z-score (median and MAD, ≥ 8 weeks of history, same weekday) on daily orders, net, fee rate and refund rate; alert at |z| ≥ 3.5 with a dollar floor. (Moves the digest's "robust-z anomalies" from "Later" to Today alerts once history exists.)
3. **Customer analytics**: repeat-buyer rate, monthly cohorts, contribution per buyer at 90/180/365 days, 5 RFM groups; Shopify first; Amazon never; Etsy, TikTok and Walmart only after compliance review; counts only, no buyer lists.
4. **Cash view** (the same need as the PM's backlog B-152; file as one request, horizon 4 or 13 weeks is the PM's call): opening cash entered by the shop, expected payouts from each channel's payout lag, open POs, run-rate costs; labelled as a projection from the last 8 weeks.
5. **Scheduled report emails**: a monthly P&L CSV to people the owner names.

Tracks A–C of the spec (unit economics, operations, inventory, assistant tools, new digest detectors, Today actions) are argued to be inside items 5–8, 13, 14 and 17 and are not part of this request; the PM confirms that separately.

## Why (evidence)
- Pains: #6 unknown true profit, #7 stockouts and supplier shocks, #11 peak season cash and staffing (`research/03-pain-points.md`). Leading profit tools (Lifetimely, Triple Whale) sell cohorts, LTV and RFM as their core; print-shop tools (Pythias, Printavo) sell output reports (spec §2, sources linked there).
- Pilots and tickets: **0 shops have asked** (no pilot is live). Owner direction 2026-09-28: "improve the business analytics of the platform to the 100% possible level".

## Who it helps
- Goals, anomalies: all segments; small shops most (no analyst).
- Customer analytics: Shopify-heavy shops (own customers); little for marketplace-only shops, since marketplaces own the buyer relationship.
- Cash view: mid and large shops buying blanks ahead of Q4.
- Scheduled emails: shops with an outside bookkeeper.

## Cost and risk
- Effort: 5 cards (wave A3 in the spec). No outside data, no paid service. AI spend: none.
- **Customer analytics is the risky one:**
  - Amazon: buyer data may be used only to fulfil the order; PII deleted 30 days after delivery (research 10 R14). A name hash is derived from PII, so Amazon is excluded entirely.
  - Etsy API Terms: "MUST NOT collect data for analytics" (research 10 §3). Whether a seller's own repeat-buyer count inside the seller's tool is covered needs counsel.
  - `orders.buyer_ref` today is a hash of the buyer's name: it merges different people with the same name. A better key (keyed hash of the channel's buyer id) is a change in the orders import (backend-foundation).
  - Retention: `buyer_ref` is nulled at 18 months and on privacy redaction, which caps cohorts at 18 months.
  - Needs `threat-model-change` and compliance-officer review before build.
- Cash view: a run-rate projection, not a statistical forecast; `decisions/0006` stands. Risk: owners read it as a promise. Mitigation: fixed label and the assumptions shown on screen.
- Scheduled emails: blocked on OI-12, OI-13 and OI-14 (address, provider, CAN-SPAM); an attachment with profit data is sensitive if sent to a wrong address (owner-only recipients setting).
- Anomaly alerts: noise with short histories; gated on ≥ 8 weeks per shop.

## If we don't
Shops keep the in-scope analytics (spec tracks A–C): profit ladder, leakage, shipping margin, operations, inventory, assistant and digest. They don't get targets, early anomaly warnings, customer retention numbers, a cash view, or reports mailed to a bookkeeper; the bookkeeper hand-off stays a manual CSV export.

## Decision
Sent to owner (OI-18).
Reason:   Decided by:   Date:

My recommendation: approve 1, 2 and 4 now for wave A3; approve 3 only after the compliance-officer's review (Shopify-only first release); leave 5 until OI-12/13/14 are answered.
