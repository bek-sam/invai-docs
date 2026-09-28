---
name: acceptance-tests-pre-contract
description: Writing acceptance tests before a contract/module lands — the dynamic-import trick, checking mid-session drift, and where a spec's ACs can be wrong about what the contract actually returns
metadata:
  type: project
---

- 2026-09-27 wave 19 (digest, T-19-1/T-19-3 not yet landed at write time): reused wave 18's pattern
  for "test the future API today" — dynamic `import(pathConstant)` for a module that doesn't exist
  yet (typechecks fine, fails at runtime with a clear "Cannot find module" reason), and a
  `procedureAt()`/`rpc()` helper that walks the *existing* top-level router by dotted path so a
  missing sub-router throws a named, readable error instead of a TS compile error. Lets QA commit
  real, running (red) test files before any builder code exists, per `acceptance-tests-first`.
  **How to apply:** for the next pre-contract wave, start from this shape rather than reinventing it;
  grep the target repo for an existing `*.acceptance.test.ts` from the previous wave first.
- Contracts can land **mid-session** while acceptance tests are still being written. Re-run the suite
  after any sibling card reports done, even if your own card doesn't depend on it directly — it can
  quietly turn "module not found" into "wrong field name", which is a real bug in the *test*, not
  progress. Concretely: `wave.md`'s "Agreed interfaces" section only fixes the names that cross card
  boundaries; internal shapes (a `Digest`'s `glance`/`marketWatch`/`planUsage` fields, whether a fact
  is a flat value or `{current, previous, changePct}`) are only knowable once the contract file
  actually exists — import the real types from `@invai/contracts` and stop guessing the moment it's
  possible.
  **Why:** wave 19's first draft used `glance.netCents`, `.market`, `.plan` — all wrong once contract
  0.7.0 landed (`net.value`, `marketWatch`, `planUsage`). Caught by re-reading the schema file, not by
  a test failure (both the guess and the real shape "fail" identically pre-build, so a wrong test
  looks the same as a right one until the real router exists).
- A spec's Given/When/Then can assume a UI/data shape that the actual contract doesn't have. Wave 19
  AC13 ("Spanish rendering") assumed a server-rendered string; the landed contract instead returns
  `DigestFact.formatted.{en,es}` on *every* fact to *every* viewer, and the client — not the server —
  picks which one to show. When this happens, split the AC across layers rather than force a backend
  test to check something backend can't produce: the backend test checks both languages are present
  and distinct, the browser spec checks which one actually renders.
- A market-sourced item's vote is not always the same procedure as a same-looking "insight" vote.
  The digest contract's own doc comment said `DigestInsight.recommendation`-backed items vote through
  `market.recommendations.vote` (wave 18, already real), never `digest.feedback` — read every doc
  comment on a reused/shared type before assuming the obvious procedure name is right.
