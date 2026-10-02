---
name: bullmq-requeue-review
description: BullMQ 6.3 facts for reviewing stable-jobId requeue logic (states, remove throws, retry goes to delayed)
metadata:
  type: project
---

2026-09-30 T-P2-5: BullMQ 6.3.8 `Job.remove()` throws "locked by another worker" when the remove script returns 0 (active job); `getState()` adds `unknown`. A retryable failure sits in `delayed`, so `failed` means final. Stable-jobId requeue (getState → remove → add) is safe only if the DB has a unique guard (e.g. `today_action_sets (company_id,date)` onConflictDoNothing).

**Why:** the remove-then-add race between two sweeps can remove a fresh or completed job and re-add it; correctness rests on the DB guard, not BullMQ.
**How to apply:** for any requeue-after-failure card, confirm the handler's DB idempotency and that the rebuild path doesn't pass `force`/delete user data. Run the new test on the base commit via `git archive` to prove red.
