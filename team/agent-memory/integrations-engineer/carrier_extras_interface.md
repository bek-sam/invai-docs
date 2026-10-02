---
name: carrier-extras-interface
description: New carrier calls go on CarrierExtras (carrierExtras()), not CarrierAdapter, to avoid breaking ~7 test fakes owned by others (T-22-3)
metadata:
  type: project
---

2026-09-29 T-22-3: adding required methods to `CarrierAdapter` broke 7 test fakes in shipping tests and acceptance tests (other owners). Address checks and SCAN forms live on `CarrierExtras`, selected by `carrierExtras(scope)` in `src/integrations/carriers/index.ts` (same live/mock/sample-workspace rule).

**Why:** respect-ownership; widening a shared interface forces edits in qa/backend-engineer test files.
**How to apply:** put new carrier capabilities on `CarrierExtras` (or a sibling interface); tests mock `carrierExtras` with `vi.mock` like they mock `carrierAdapter`.
Also: test DBs copied from `invai_test` go stale if another card's uncommitted migration was applied to them; drop and recreate from the template after that card commits.
