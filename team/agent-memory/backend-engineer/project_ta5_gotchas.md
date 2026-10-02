---
name: project-ta5-gotchas
description: T-A5 backend gotchas — raw-SQL timestamptz casts, 365-day sale window, owned-file-without-owned-test pattern.
metadata:
  type: project
---

From building `analytics.inventoryHealth`/`supplierTrends`/`designLifecycle`/`export` (T-A5, wave A1):

- A raw `sql` template with a JS `Date` bind param used in interval arithmetic (`${t} - interval '28 days'`) fails with `operator does not exist: timestamp with time zone >= interval` — Postgres can't infer the untyped param's type. Cast explicitly: `${t}::timestamptz - interval '28 days'`.
- `design_lifecycle.sql`'s `sales` CTE only looks back 365 days (`o.placed_at >= t - interval '365 days'`), so a test fixture's "old first sale" meant to predate the 8-week "new" cutoff must still fall inside that 365-day window, or it's invisible and `first_sale` becomes whatever recent sale remains (silently flips the stage to "new").
- When a card grants an edit to one file (e.g. `inventory/reorder.ts`) but not its usual test file (`inventory/reorder.test.ts`, owned by another card), tests for the new pure function belong in your own owned `*.test.ts` (imported from the ungranted file) rather than editing the other test file. See [[feedback_containment_vs_equality_tests]] for related test-design judgment calls.
- 2026-09-30 T-A5 r2: `getTrendSignal({designId})` falls back to the niche's outside readings; the design's own trend is `readings[].provenance.source === "own"`. To prove "fails before fix" in the shared tree, use a scratch `git worktree add --detach` at HEAD + copied `.env` + symlinked node_modules, run `./node_modules/.bin/vitest` (pnpm exec tries to reinstall).
