---
name: analytics-v2-scope-check
description: business-analytics-v2 spec (waves A1/A2) fits items 5/6/7/8/13/14/17; Track D (B-178..181) gated on OI-18; B-183 is verify-first
metadata:
  type: project
---
2026-09-28: reviewed `specs/business-analytics-v2.md` and backlog B-168..B-183 against `product/scope.md`.
Verdict written to `invai-docs/waves/analytics-scope-check.md`.

- B-168..B-177 (Track A/B/C, waves A1/A2) fit inside existing items 5, 6, 7, 8, 13, 14, 17 — no SCR needed,
  no fence hit (dest_zone is a zone number not an address; reorder size-split and Today actions are
  suggestion-only).
- B-178 (goals), B-179 (anomaly alerts), B-180 (customer analytics, buyer PII), B-181 (scheduled emails) stay
  out of A1/A2 — gated on owner OI-18 (open, deadline 2026-10-09). B-181 additionally needs OI-12/13/14.
- B-183 (Amazon CSV $0 shipping) is verify-first: if integrations-engineer confirms a parser bug it's
  always-in-scope regardless of this wave; if it's genuinely absent from Amazon's export, it's just a caveat
  update to `shipping_margin.md`.
- Spec status was "draft for product-manager review" — not `ready` yet: missing logged reviews from
  product-designer, qa-engineer, customer-success (write-spec requires these before handoff). None of the
  spec's 5 open questions block A1/A2 itself.

**Why:** tech lead asked for scope confirmation before planning; this is the record so future waves don't
re-litigate which analytics-v2 rows are in scope.

**How to apply:** when the tech lead plans wave A1/A2 cards, check the three reviews got logged in the spec
before treating it as `ready`. Don't plan B-178/179/180/181 until OI-18 (and for 181, OI-12/13/14) is
answered. See also [[market-digest-fences]] for the sibling OI-9..14 pattern this follows.
