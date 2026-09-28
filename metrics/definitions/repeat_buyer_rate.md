# Metric: repeat_buyer_rate

- **Label:** EN "Repeat buyers" / ES "Compradores que vuelven"
- **Version:** 1 DRAFT (2026-09-28), not approved for build   **Owner (acts on it):** product-manager   **Defined by:** data-analyst
- **Spec:** `specs/business-analytics-v2.md`

## Meaning
Of the people who bought from you for the first time in a period, the share who bought again within 90 days.

## Formula
- Numerator: first-time buyers in the cohort window with another order within N days (default 90) of their first.
- Denominator: buyers whose first order falls in the cohort window.
- Buyer = `orders.buyer_ref` (a company-scoped hash; never decoded or output).
- Excludes: Amazon (buyer data only for fulfilment; DPP), cancelled orders; channels compliance hasn't cleared (see caveats).
- Unit: percent.
- Minimum sample: 30 new buyers per cohort row.

## Source
| Table.column | Meaning |
|---|---|
| orders.buyer_ref, placed_at, channel, status | buyer identity (pseudonymous) |

## Marketplace comparison
None: this is InvAI's own number; no marketplace defines it.

## SQL
Path: `invai-docs/metrics/sql/repeat_buyer_rate.sql` (moves to `invai-backend/scripts/analytics/` with B-49; see `metrics/definitions/README.md`).
Tested 2026-09-28 on the local dev DB `invai` (shared seed, read-only SELECT, sample workspaces excluded), window 2026-08-28 → 2026-09-29 unless stated. Result below is **SEED** data, not a business result.
- etsy 144 new buyers, 0 repeat; shopify 112, 1 repeat (0.9%); tiktok 47, 0. The seed has no repeat behaviour (and only ~30 days).

## Cuts
| Cut | Valid? | Notes |
|---|---|---|
| Segment (small / mid / large, `shop_segment.md`) | Yes | Report per segment only when the cell has ≥ 3 shops; otherwise per shop slug |
| First channel | Yes | |
| First design / niche | Yes | 'which designs bring buyers back' |
| Cohort month | Yes | ≤ 18 months back (retention) |

## Target and alarm
- Target: PM to set after pilots
- Alarm (goes into the weekly review): none until defined

## Caveats
- **DRAFT, gated (`metrics/scope-change-draft-analytics-v2.md`, owner-inbox OI-18):** customer analytics is not in scope item 8 and needs compliance-officer review before any build.
- `buyer_ref` today is a hash of the buyer's *name*: common names merge different people and one person on two channels counts twice. Proposed: a keyed hash of the channel's buyer/customer id where the channel gives one (Shopify customer id, Etsy buyer_user_id), name-hash fallback labelled 'approximate'.
- `buyer_ref` is nulled by the 18-month retention sweep and on privacy redaction; cohorts older than that can't exist.
- Etsy API Terms say not to 'collect data for analytics' (research 10 §3); whether the shop's own repeat-buyer count counts is a counsel question. CSV exports are the shop's own data.
- PII: the query reads no `buyer_pii`, buyer notes, addresses or personalization text; output is shop slug, channel, ids and numbers only.

## Change log
| Version | Date | Change | Why |
|---|---|---|---|
| 1 | 2026-09-28 | First definition | Analytics v2 audit (owner direction 2026-09-28) |
