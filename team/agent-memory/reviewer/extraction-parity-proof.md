---
name: extraction-parity-proof
description: How to prove a "refactor only, output unchanged" claim (e.g. shared computeNet extraction) cheaply and decisively
metadata:
  type: feedback
---

2026-09-30 T-A3: to prove "getProfit output unchanged" after an extraction, `git archive <base>` into a sibling dir (symlink node_modules, copy .env), run one `.mts` script that dynamic-imports `${root}/src/...` and dumps the function's JSON for a grid of inputs (dimensions x filters x periods, stable sort), run it with root=base and root=HEAD against the dev DB (read-only), and `cmp` the outputs. Check whether the dev data exercises every branch (here: 0 refund_events, so the refund path relied on reading the moved code).

**Why:** tests passing both before and after doesn't show that the numbers are identical; a byte-identical dump does, in about 2 minutes.
**How to apply:** any card that claims an extraction or refactor leaves output unchanged. Related: [[env-backend-worktree-review]].
