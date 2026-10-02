---
name: seed-analytics-gaps
description: Non-obvious facts about the local seed and schema that break or distort analytics queries (checked 2026-09-28)
metadata:
  type: project
---

- Seed has ~30 days of history: every design is "new", turns are understated, cohorts impossible (B-130 / B-168 fix).
- Press scans share identical timestamps (synthetic): measured press time returns 0 timed units; stage waits all show median 5.0 h.
- Shared dev DB had 0 late shipped orders on 2026-09-28 (43 overdue open): late-driver cuts can't be validated.
- No purchase orders in the seed: supplier trends return 0 rows.
- `orders.buyer_ref` = sha256 of the buyer *name* (company-scoped); nulled at 18-month retention and on redaction.
- Amazon seed orders have `shipping_cents = 0` (B-183).
- Profit page Net = Σ profit_lines.net − refund_events (by refunded_at) + fee_recovered; `profit_lines.refunds_cents` is only the cancel reversal. Many orders have no profit line (report `ordersWithoutProfitLine`).
- Real-shop filter = `demo_owner_user_id IS NULL AND settings->>'demoRetiredAt' IS NULL` (realCompanySql); Desert Bloom counts as real, the `demo-<uuid>` company does not.
- Agent memory must be written under `/Users/bekbolsun/invai/.claude/agent-memory/data-analyst/` (a hook blocks the invai-docs/.claude path).

**Why:** these made seed numbers misleading during the analytics v2 audit.
**How to apply:** label seed results SEED, and check these before trusting a surprising number. Related: [[project-analytics-v2]].
