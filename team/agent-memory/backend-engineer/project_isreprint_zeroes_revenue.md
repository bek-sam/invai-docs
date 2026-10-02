---
name: project-isreprint-zeroes-revenue
description: isReprint = "re-pressed" (decision 0020); fixed in T-P4-1 — every reader that filtered it out of units/revenue was wrong. Metric SQL docs and fixtures may still assume the old sibling-row model.
metadata:
  type: project
---

Decision 0020 (2026-10-01): `isReprint` on order_items/profit_lines/transfers means "re-pressed at
least once"; never filter it to count units, revenue, refunds, demand or re-import matching.
T-P4-1 (commit 8d69b64) removed the filters in finance, refunds, orders/import, analytics, market.

**Why:** `openReprint` flips the flag on the same row; no sibling reprint item ever exists. The old
filters gave $0 revenue on 44 seed orders and let re-import add a second unit to ship.

**How to apply:** if you see `not is_reprint` in a unit/revenue query, it's a bug. Leakage reprint
cost = blank + transfer_cost/(1+reprints) assumes the item holds all its transfers. Data-analyst's
`invai-docs/metrics/sql/*.sql` (profit_bridge, size_mix_gap, design_lifecycle) were still on the old
model at T-P4-1 time; finance-parity.test.ts compares service vs those files.
