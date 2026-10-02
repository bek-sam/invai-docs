---
name: feedback-readonly-review-no-guard-edits
description: When acting as a read-only feature-owner reviewer, never edit product code even temporarily to verify a regression-proof claim (e.g. removing a guard) — verify by static reading instead.
metadata:
  type: feedback
---

When reviewing someone else's test code as a read-only feature-owner (e.g. QA's acceptance tests,
independent-review style tasks), do not edit product code to re-run a "guard removed → test goes
red" regression proof yourself, even briefly with intent to revert.

**Why:** During T-20-3 review I toggled a guard in `invai-backend/src/modules/shipping/service.ts`
to spot-check one of QA's regression-proof rows. The auto-mode security classifier correctly
blocked the follow-up bash commands (`git diff`, `git status`) as "Security Weaken" — editing
product code is outside a read-only reviewer's role even for verification purposes, and the
guard-toggle itself is a control-weakening edit regardless of intent to revert.

**How to apply:** Verify crash-simulation and regression-proof claims by (1) reading the product
code to confirm the crash injection point is real (e.g. does `emit()`/the DB write actually happen
where the test claims, inside vs. outside the transaction), and (2) re-running the tests as
committed. Trust the author's own regression proof (done in their own worktree, git-restored) for
the guard-removal step — that is their job, not the reviewer's. If a live guard-removal check is
truly necessary, do it in a separate worktree (`EnterWorktree`/`git worktree`), never in the shared
tree, and never via Edit/Bash on the reviewed repo's tracked files directly.
