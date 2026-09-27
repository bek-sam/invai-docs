---
name: s34-taxonomy-equality-test
description: When a card requires "the fetched set equals X", check the test asserts equality, not just containment — a containment-only test misses a narrowed-subset regression
metadata:
  type: feedback
---

On T-18-3 (wave 18, market signals), the card's S-34/AC2b required a test asserting the
`refreshDemand` job's fetched query set **equals** the full niche taxonomy (so a cache row's
presence/freshness can never become a per-tenant signal, per ADR 0015 global-market-cache).
The author's test (`service.test.ts` "refreshDemand stores only taxonomy queries...") only
asserted **containment** (every stored query ∈ taxonomy), not equality. The production code was
actually correct (`const queries = [...CANONICAL_QUERIES]` unconditionally) — but a
containment-only test would pass unchanged if a future edit narrowed `queries` to a
tenant-derived subset, which is exactly the regression the card was guarding against.

**Why:** "no query outside the taxonomy" and "every query in the taxonomy" are different claims;
only the second guards against a scope-narrowing regression. A reviewer reading only "the test
exists and passes" would have missed this.

**How to apply:** whenever a card/finding says a fetched/read/queried set must equal a fixed
reference set (not merely be a subset of it), check the actual assertion is `toEqual`/set-equality
in both directions, not a per-item `.has()`/`.includes()` loop. If it's containment-only, that's a
blocking finding even when the underlying code is already compliant — write your own equality test
in an isolated worktree to prove the code is compliant today (so it's a test gap, not a live bug),
then block until the real suite gets the equality assertion.

**Round 2 (verified, S-34 closed):** the author fixed it with a capture hook (`onQueries`) recording
the exact argument passed into `provider.series()`, asserting `toEqual(CANONICAL_QUERIES)` — real
Set-equality, containment check kept alongside it. To verify a fix like this actually catches the
regression (not just "the assertion exists and passes today"), make the regression itself as a
local, uncommitted edit in your own detached worktree (e.g. narrow the query list to half the
taxonomy), confirm the test now fails, then restore with `git show HEAD:<path> > <path>` — never
`git checkout`/`reset` in a shared tree, `guard-bash.py` blocks it even in your own worktree.
