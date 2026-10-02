---
name: migration-review-notes
description: Co-review precedents for when a migration needs SET LOCAL lock_timeout, CONCURRENTLY, or a composite FK, and when it's fine without
metadata:
  type: feedback
---

Accumulated precedents from co-reviewing migrations 0032-0037 (T-22-3, T-22-4, T-22-5, T-A3/T-A4),
plus the T-19-3 drift-check trick.

- **New empty table, FK to a big table (orders/companies):** validates instantly — `checklist.md`
  treats "create a new table" as safe-as-one-step, distinct from "add FK to an existing big table".
  Missing `SET LOCAL lock_timeout` here is not blocking (0026-0029, 0033 all omit it too).
- **No-default nullable `ADD COLUMN` on PG ≥11:** metadata-only, so `SET LOCAL lock_timeout` is
  optional even on a growing table (`shipments.dest_zone`, `cost_settings.fixed_monthly_cents`).
- **One-row-per-company table doing a filtered `UPDATE`** (`cost_settings`,
  `uniqueIndex().on(companyId)`): also non-blocking without `lock_timeout` — same precedent class.
- **Partial unique index as a guard:** `(company_id, station_id) WHERE ended_at IS NULL` doubles as
  both the "one open window" invariant and the exact index needed for the "open window at this
  station" lookup. Reusable pattern for any open/active-window table.
- **Appending values to `text(enumText(...))`:** zero-risk, no migration SQL needed at all (no pg
  enum, no CHECK) — unlike a real pg enum or CHECK-constrained column.
- **Array columns can't carry a real FK** (e.g. `scan_forms.shipmentIds`) — check for an existing
  precedent (`shipments.orderItemIds`) before calling that a gap.
- **`--custom` data-only migrations** are verifiable without reading the SQL: diff
  `meta/<N>_snapshot.json` before/after — `tables`/`policies` byte-identical plus `prevId` chaining
  to the prior `id` proves no schema drift, only data changed.
- **A 3-part unique index is not automatically the idempotency key**: `(company_id, gang_sheet_id,
  seq)` with `seq` incrementing per attempt (send=1, resend=2) is a DB-level backstop, not the real
  guard — the real guard is a row lock on the parent (`lockSheet`) serializing concurrent resends.
- **Drift-check trick** (also T-19-3): `drizzle-kit generate --name <scratch>` in a disposable
  worktree, against a DB migrated from zero, reporting "No schema changes, nothing to migrate"
  proves `schema.ts` and the committed SQL match exactly — stronger than trusting a shared dev DB
  that had the migration pre-applied by someone else.
- Always check `git log -1` right before a review run — commits landing mid-run cause spurious
  failures.
