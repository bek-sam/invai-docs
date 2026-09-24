# T-1-5: A fresh production database has its reference data

| Field | Value |
|---|---|
| Wave | 1 |
| Scope ref | `product/scope.md#mvp-in` item 11 (bug) |
| Backlog | B-54 |
| Owner | ai-engineer (with the migrate hook granted on this card) |
| Reviewer | reviewer |
| Co-reviewers | backend-foundation |
| Risk flags | migration |
| Model | sonnet |

## Owned paths (edit)
- New `invai-backend/src/db/reference/**`
- `invai-backend/src/db/migrate.ts` (only to call `ensureReferenceData` after migrations)
- `invai-backend/src/db/seed/index.ts` (only to stop inserting trademark marks there, now that reference data does it)
- tests next to these files

## Evidence
`build/audit-2026-09-24.md` §A-BE B-54.

## Acceptance criteria
1. `ensureReferenceData(db)` upserts the trademark marks and the plan catalog. It's idempotent, creates no tenants and is safe to run on every deploy. It runs at the end of `runMigrations`, so `pnpm db:migrate` on an empty DB leaves the trademark check working.
2. The marks move from the seed into versioned reference data. The seed still produces the same demo results.
3. A test: migrate an empty test DB, then run a trademark check on a known mark (for example "Disney"), and it comes back high risk.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test` in invai-backend, with your own test DB.
- Create an empty DB, run migrate with `MIGRATION_DATABASE_URL` pointing at it, and query the `trademark_marks` count.

## Out of scope
- A USPTO bulk loader (later). The B-46 gate (wave 8).
