---
name: floor-late-result-double-apply
description: Floor "late server answer replaces provisional view" features - check the live (non-queued) path doesn't re-apply and re-beep; render-probe recipe
metadata:
  type: feedback
---

2026-09-30 T-P3-2: the floor `submit()` goes through `flushOutbox`, so anything a flush "publishes" (e.g. `resolved` by clientScanId) also fires for normal online scans. A panel effect that applies late results without checking `view.provisional || view.queued` re-applies the live result and calls `feedback()` twice: double beep on every scan.

**Why:** the reducer and engine unit tests passed; only a component render showed it.

**How to apply:** for any floor late-result or subscription feature, render the station in a /tmp `git archive` copy (symlink node_modules). Use mocks shaped like `QcStation.test.tsx`, plus mock `useSession`, `Thumbnail`, `findCachedItem` and `cachedBlanks`. Have the `submit` mock publish to the store the way the flush does, and count `feedback` calls. Run vitest with `--silent=false` to see console.log output.

2026-10-01 T-P3-2 r2: fix pattern that passed = effect still takes the resolved entry but applies/beeps only when view.provisional||queued. When reviewing TTL pruning of such entries, check the timestamp it ages from is set at the publishing send (outbox.ts sentAt), not at enqueue — otherwise a long-busy scan's verdict could be pruned on arrival.
