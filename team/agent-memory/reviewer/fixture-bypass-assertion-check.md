---
name: fixture-bypass-assertion-check
description: When a test helper writes derived rows directly (e.g. digest saleAt -> profit_lines), a value assertion like net can't catch a product-rule regression; probe with old product files
metadata:
  type: feedback
---
2026-10-01 T-P4-5: digest.acceptance AC10's reprint check (`net === 500`) passed with all T-P4-1 product files reverted, because `saleAt` inserts profit_lines revenue/cost directly and net is just their sum. A units assertion (`getProfit(...).totals.units`) was the discriminating check (red on old, green on new).

**Why:** fixture-model rewrites can look like model corrections yet assert only the fixture's own arithmetic.
**How to apply:** for "fixture follows decision X" cards, build a /tmp worktree, write old product files with `git show <base>:path > file` (guard hook blocks `git checkout -- path`), run the changed tests; if green, probe one extra assertion in the worktree to give the owner a proven fix. See [[extraction-parity-proof]].
