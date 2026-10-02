---
name: wave22-25-plan-review-findings
description: Recurring plan-review patterns found reviewing waves 21 (T-21-5), 22, 23, 24, 25 (2026-09-28)
metadata:
  type: project
---

Findings worth re-checking on future wave-plan co-reviews.

- **Field-name collisions across shared schema types.** `QueueItem`/`ScanResult` in
  `invai-contracts/src/schemas/production.ts` already have a `binCode` field (the order's pack
  tote/bin, from `bins.assign`). A card asking to add "the blank's bin location" to the same pick
  line (B-32) would silently collide if named `binCode` again — it needs its own name or to nest
  under the existing `blank: {...}` object. Always grep the target schema file for the exact field
  name a card proposes before approving it.
- **"A scan never errors for business outcomes" applies to every new blocked-scan case, not just the
  ones already in `MISMATCH_REASONS`.** A card proposing a new "error code" for something that can
  happen during a `production.scan` call (station under maintenance, etc.) should almost always be a
  new `MISMATCH_REASONS` value returned via `ScanResult`, not a thrown `.errors()` code. Check this
  every time a card's phrasing says "returns an error" for anything that fires during a floor scan.
- **Same-file, split-by-hunk ownership across cards needs an explicit "committed, not just
  generated" gate.** Wave 22 had T-22-2 owning FK/index hunks and T-22-4/T-22-5 owning new-column
  hunks in the *same* `src/db/schema/*.ts` files. The wave plan sequenced migration *generation*
  order but not the underlying file edits — a real concurrent-edit risk if the later cards start
  before the earlier one's schema commit lands, not just before it generates a migration.
- **New feature state doesn't automatically belong to the module whose contract namespace it reads
  most naturally under.** Station maintenance (proposed under `production.*`) actually wanted to
  live on the `stations` table, which lives in `tenancy.ts`/`src/modules/tenancy/**` — a module no
  card in the wave owned. Check which schema file/module a proposed feature's state would naturally
  attach to (grep for the entity's table), not just which contract namespace its procedures sit
  under; they can differ, and a new production-owned table is often the cleaner fix.
- **`CREATE INDEX CONCURRENTLY` cannot run inside `pnpm db:migrate`** (`drizzle-orm`'s `migrate()`
  wraps every pending migration in one transaction, and Postgres refuses `CONCURRENTLY` inside a
  transaction block) — and no `drizzle/online/` runner exists yet in this repo. Pre-launch (no live
  shop traffic), a plain `CREATE INDEX` in the normal migration is fine; say so explicitly in any
  card that adds an index, so the implementer doesn't reach for `CONCURRENTLY` and get a hard
  failure.
- **A "trace X → Y → Z" observability card can name a repo its owner doesn't own.** T-25-4
  (backend-foundation, "OTel traces API → queue → imaging") needs spans inside
  `invai-imaging/app/main.py`, which is imaging-engineer's repo. Check every "traces through
  <service>" or "propagates to <service>" card for whether completing the chain requires editing a
  repo outside the assigned owner's fence; if so it needs a grant/co-reviewer or an explicit
  narrower scope.
