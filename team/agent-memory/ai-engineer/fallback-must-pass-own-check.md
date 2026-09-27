---
name: fallback-must-pass-own-check
description: Assistant market tools' code-written answers are the gateway's fail-closed fallback, so each must pass validateAnswer alone; record eval baselines only from a fresh migrated DB
metadata:
  type: feedback
---

2026-09-27 T-18-4 r2: A tool's code-written `answer` is what `fallbackAnswer()` shows when the model's draft fails the check twice. Every market tool answer, including unavailable and insufficient branches, must pass `validateAnswer` on its own: "Sample data" on mock sources and a date on outside sources.

**Why:** r1 was sent back because `simulate_price` and `get_price_position`'s unavailable branch left out the mock disclosure. The committed baseline said 19/21, but a fresh DB gave 15/21.

**How to apply:** For any new assistant tool or branch, add a test that runs the fallback through `validateAnswer` with mock sources. `marketOutput`'s `disclosure()` is the safety net. Record `evals/baseline.json` only from a run on a freshly migrated DB in a clean worktree, not from the shared tree. See also [[eval-harness-notes]].
