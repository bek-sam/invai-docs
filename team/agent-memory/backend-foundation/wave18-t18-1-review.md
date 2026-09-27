---
name: wave18-t18-1-review
description: T-18-1 (market contract + ADR 0015) co-review notes — worktree typecheck trick and ADR/table consistency check
metadata:
  type: project
---

2026-09-27 T-18-1 co-review (approve, round 1): the architect's ADR 0015 (global `market_series_cache`
table, no `company_id`) matched `src/db/schema/market.ts` exactly once T-18-3 landed — same columns,
`publicReadPolicy()` + `.enableRLS()`, unique index `(source, query, granularity, period)`, and both
`PUBLIC_READ_TABLES` and the app-role-write-denial list in `rls-coverage.test.ts` already carried
`market_series_cache`. Precedent (`trademark_marks`) held up as the model to check against.

**Why:** the card asked to verify the ADR's promises "hold" against how `trademark_marks` and
`rls-coverage.test.ts` actually work, not just that the ADR text is internally consistent — worth
diffing the ADR's claims against the real committed schema/test file even when reviewing a
contracts-only card, since the wave's later cards (T-18-2/3/4) had already landed on the shared
tree by review time.

**How to apply:** when co-reviewing an architect's ADR that describes a table/migration another
card will build, check the *actual* schema file if it already exists in the shared tree (git log
often runs ahead of the wave.md "planned" status) — don't just read the ADR in isolation.

Verification trick used: to typecheck invai-backend against exactly the card's contract version
without touching the shared tree, `git worktree add ../invai-backend-<tag> <sha>` at the first
commit where the backend compiles against the new contract (here `7ed3b4f`, the T-18-3 stub that
adds `market: marketRouter`), then `ln -s <real-repo>/node_modules node_modules` (relative
`@invai/contracts` symlink inside it still resolves correctly since its target is relative to its
own real parent dir, not the worktree), run `node_modules/.bin/tsc --noEmit` directly (never
`pnpm` in a worktree), then `git worktree remove --force` and move on. Confirmed clean with no
`pnpm install`.
