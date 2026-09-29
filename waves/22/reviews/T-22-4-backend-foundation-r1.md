# Review of T-22-4 (round 1) — migration only

- Reviewer: backend-foundation on Sonnet 5
- Author: backend-engineer on claude-opus-5-5
- Verdict: approve

Scope: invai-backend commit `08d1eba` (migration 0033) and its hunks in `src/db/schema/{production,inventory}.ts` only.

## Evidence I re-ran
| Command | Result |
|---|---|
| Fresh DB `invai_t22_4m`, global-setup migrate-from-zero, `vitest run --reporter=dot src/db` | 9 files, 31 passed |
| `vitest run --reporter=verbose src/db/rls-coverage.test.ts src/db/fk-coverage.test.ts` | 10/10 passed, incl. new table |
| `drizzle-kit generate --name t22_4m_drift_check` against migrated DB | "No schema changes, nothing to migrate" |
| `psql \dp station_maintenance_events` | `invai_app=arwd` (default grants), tenant policy present |
| `git show 08d1eba --stat` / SQL read | 0033 SQL matches schema hunks; journal/snapshots 0030→0033 sequential |

## Checklist
- `station_maintenance_events`: `company_id`, `tenantPolicy()`, `.enableRLS()` all in this migration. RLS coverage test passes green with it included.
- FK to `stations` is composite `(company_id, station_id) -> stations(company_id, id)`, matching rule 5; `stations` already carries the required `unique(company_id, id)` via `tenantKey`. `fk-coverage.test.ts` confirms no single-column tenant FK regression.
- Indexes lead with `company_id`: partial unique `(company_id, station_id) WHERE ended_at IS NULL` (also serves "open maintenance for a station" directly), plus `(company_id, station_id, started_at)` and `(company_id, started_at)`.
- `stock_levels.bin_code`: nullable `text`, no default — metadata-only `ADD COLUMN`, no rewrite, no lock risk.
- REPRINT_REASONS `under_cure`/`cracking`: appended via `enumText()` (app-level typing only, no DB CHECK/enum type), so no migration SQL touches `reprints` — additive, zero risk, one transaction. Mirrors contracts `83013af`'s `MAINTENANCE_REASONS`/reason values, confirmed present in linked `@invai/contracts`.
- New table created empty in this same migration, so the non-`CONCURRENTLY` unique/plain indexes and the FK validate instantly; no `SET LOCAL lock_timeout` guard needed (same as 0032 precedent, T-22-3 r1).
- Grants: default privileges from `0001_grants_extensions.sql` cover the new table; not append-only, so no REVOKE needed.

## Blocking findings
None.

## Optional notes (not blocking)
- `reason`/`note`/`endNote` have no length cap; fine for a small enum-backed free-text field, not a migration concern.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
