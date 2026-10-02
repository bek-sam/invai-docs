---
name: offline-scan-time
description: Floor scan checks must evaluate time-dependent rules (maintenance windows, etc.) at the scan's scannedAt, not now, because the tablet outbox replays offline scans later
metadata:
  type: feedback
---

Any rule on the floor scan path that depends on time (station maintenance windows, holds) must be evaluated at `input.scannedAt` as well as now; the offline Dexie outbox replays scans after the fact.

**Why:** T-22-4 r1 was blocked because the maintenance block only checked "window open now"; an offline scan made during a window pressed after replay.

**How to apply:** For a new scan-time guard, query "open now OR covered scannedAt" and add a test with a past scannedAt inside a closed window. See [[backend-gotchas-w19]].
