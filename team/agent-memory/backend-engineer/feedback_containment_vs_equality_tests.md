---
name: feedback-containment-vs-equality-tests
description: When a test must guard against future narrowing of a fetched/stored set, assert Set-equality against the canonical set, not just containment
metadata:
  type: feedback
---

On T-18-3 (market module) round 2, security review blocked on a test that only asserted
containment (`every stored query ∈ CANONICAL_QUERIES`) where the acceptance criterion (S-34)
required equality (`the fetched set == CANONICAL_QUERIES`). A containment-only test doesn't catch
a future regression that narrows the fetched/stored set to a subset — every existing assertion
still passes on a subset.

**Why:** S-34 exists because `market.refreshDemand` must fetch the whole fixed taxonomy every
run, never a tenant-derived subset (a narrowed fetch would let a cache row's presence/freshness
leak a low-fidelity cross-tenant signal). The safety property here is exact coverage, not "no
extra junk got in".

**How to apply:** when a card or security finding says a test must assert a fetched/stored set
"equals" a canonical set (not "is limited to" or "only contains"), write the assertion as
`expect(new Set(actual)).toEqual(canonicalSet)`, and capture the *input* to the collaborator under
test (e.g. the `queries` argument passed into a provider's `series()` via a test double's capture
hook) rather than only inspecting what ended up persisted — the two can diverge if a bug is
downstream of the fetch.
