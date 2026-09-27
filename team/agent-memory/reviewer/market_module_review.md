---
name: market-module-review
description: Notes from reviewing T-18-3/T-18-4 (market signals module and assistant tools) — useful for future market/wave-18 review rounds
metadata:
  type: project
---

2026-09-27 T-18-3 r1: oRPC RPC wire format for this repo needs `POST` with body `{"json": <input>}`, not a GET
query string — a bare `{...}` body 400s with "expected object, received undefined" even though the error
message itself echoes back `{"json": {...}}`. Useful for any future card exercising `/rpc/*` by curl.

2026-09-27 T-18-3 r1: the cross-card finding "`simulate_price` returns candidate prices 100x too large"
(wave 18) was a real bug: `history.ts`'s `currentPrices` multiplied an already-cents `ProductPrice.price` by
100 again. Confirmed fixed in c2057df by hand-calculating margin at two price points against the live seed
and matching to the cent. Good pattern for any money-in-cents review: don't just check the type, recompute
one row by hand against the exact formula in the spec.

2026-09-27 T-18-3 r1: `scan-test-weakening.sh` runs over the whole `origin/main..HEAD` diff, which in a
multi-card wave includes every other card's commits too. Filter its output to the card's own commits (check
each hit's file against the card's owned paths) before treating a hit as a finding — most of the noise in a
5-card wave belongs to a different card.

2026-09-27 T-18-3 r1: for a global (non-tenant) cache table's security property ("fetch the whole taxonomy,
never a tenant-derived subset"), reading the job function's signature is often stronger evidence than the
existing tests: if the function that builds the query list takes no companyId parameter at all, there is no
code path by which tenant usage could narrow it, regardless of what the tests directly assert. Worth citing
in the review as non-blocking test-coverage gap rather than a correctness block, when the report is honest
about the gap and the invariant is verifiable by inspection.

2026-09-27 T-18-4 r1: `evals/market/main.ts` (and any eval `main.ts` that doesn't go through vitest) uses
`env.DATABASE_URL` directly, not `TEST_DATABASE_URL` — running it needs a real migrated copy of the dev DB
(`createdb -U invai -T invai <copy>`, then `DATABASE_URL=...  MIGRATION_DATABASE_URL=... tsx src/db/migrate.ts`,
then rerun the eval with those same env vars). Running it against the shared `invai` dev DB before the
matching migration lands 42P01s immediately.

2026-09-27 T-18-4 r1: a guardrail that "fails closed" (regenerate once, then fall back to fixed tool text) is
only as safe as its fallback text. Found a real bug by grepping every code-written `answer:` template in the
tool file for whether it includes the source/mock disclosure (`sourceLine`/`src`) that the validator requires
whenever `meta.mock` is true — two of four tools' templates omitted it, so their own guaranteed-safe fallback
still failed the validator's own check (`outcome: fallback, secondIssues: [missing_sample_label]` in the real
gateway log). General pattern: for any "fallback answer = X" design, check X against the same validator that
triggered the fallback, not just against the happy path. A direct call to the tool function with a hand-built
mock-flagged input (bypassing the LLM) reproduces this fast and deterministically.

2026-09-27 T-18-4 r1: eval baselines can silently drift stale even on the same commit — rerunning
`evals/market/main.ts` on a fresh DB copy got 15/21 plumbing vs. the committed baseline's 19/21, because the
extra failures depend on mock comparable counts that vary by DB/seed state, not just on code. Don't trust a
committed eval baseline number without rerunning it once in the review.
