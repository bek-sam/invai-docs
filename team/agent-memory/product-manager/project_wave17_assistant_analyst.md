---
name: project-wave17-assistant-analyst
description: Wave 17 (assistant-as-business-analyst) PM review status and open owner questions on the two cut ideas
metadata:
  type: project
---

Wave 17 adds 4 read-only analyst tools (`compare_periods`, `get_ad_performance`,
`get_design_insights`, `get_fulfillment_health`) plus prompt v4 (tool memory, shop
context, language, analyst mode) to the AI business assistant
(`invai-docs/specs/assistant-business-analyst.md`, scope.md#mvp-in item 13).
I reviewed the plan on 2026-09-26 and approved it —
verdict in `invai-docs/waves/17/reviews/plan-pm.md`. I confirmed the spec's status
and tightened its acceptance criteria (added AC9 small-shop/no-ads-degrade-gracefully,
AC10 disconnected-channel-flagged-incomplete), added a Segments section, Success
metrics and Open questions.

Two ideas the spec put out of scope were filed as scope-change requests and escalated
to the owner (both recommend **defer**, not reject):
- **OI-6** / `product/scope-changes/SCR-001-assistant-external-market-signals.md`:
  external market signals (Etsy/Amazon search trends, competitor prices). Risk: needs
  paid API or scraping, and scraping breaks marketplace ToS which could hurt the
  pending Etsy Commercial Access / Amazon SP-API applications. 0 shops have asked for it.
- **OI-7** / `product/scope-changes/SCR-002-assistant-weekly-digest.md`: a scheduled
  weekly push digest (vs. today's on-request-only assistant). Risk: new recurring
  per-tenant AI spend, unattended outbound content with no human check first, and it's
  a different shape than item 13's "read-only tools you ask". Wave 17 already ships
  the on-request "weekly business review" starter question, so this is genuinely a
  "wait and see if pilots use the on-request version" question.

**Why:** both ideas are plausible but unproven (no pilot evidence yet — no pilots are
live as of 2026-09-26) and both carry cost or marketplace-approval risk, which is the
owner's call per `product/scope.md` and the operating rules, not mine to decide alone.

**How to apply:** before ranking either of these in a future backlog pass, check
`owner-inbox.md` OI-6/OI-7 for an answer first. If still open, keep recommending defer
until pilot usage data exists (`weekly-metrics-review`) or the owner explicitly funds
a market-data source. Don't let a future ai-engineer or tech-lead build either one
without an owner answer — that would be building outside `scope.md`.
