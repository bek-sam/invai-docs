# Review of T-12-4 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: backend-foundation on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-contracts log --oneline -3` / `git show --stat 13e7b14` | 7 files, contract + roles + schemas as described |
| `git -C invai-backend show --stat ba9db95` / `959a037` | 12 files (service/jobs/router/zip/migration/s3/test); 2 files (files/service.ts KIND_PERMISSIONS + test) |
| `bash .claude/skills/independent-review/scan-test-weakening.sh invai-backend origin/main` | hits, none attributable to T-12-4 (T-12-1/T-12-3 mocks and a pre-existing `!env.isTest` scheduler guard pattern reused in `privacy/jobs.ts`); assertions added=305/removed=0 |
| `bash .claude/skills/independent-review/scan-test-weakening.sh invai-contracts origin/main` | no hits |
| `createdb invai_review_t124`, `NODE_ENV=test pnpm db:migrate` against it | migrated cleanly through 0026 |
| `vitest run src/modules/privacy/tenant.test.ts` | 10 passed (report said 9; +1 from the `959a037` follow-up test) |
| `vitest run src/db/rls-coverage.test.ts src/db/rls.test.ts src/api/authz.test.ts` | 20 passed |
| `grep -n "withSystem(" src/modules/privacy/service.ts` | 7 call sites, each with a reason comment on the line(s) above (cross-tenant read of ids, or the owner-connection purge) |
| Dropped `invai_review_t124` after | cleaned up |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Export trigger/status shape | Yes | `contract/privacy.ts` matches stub B verbatim; test downloads the zip via `files.downloadUrl` and checks `orders.csv` row count (3) and manifest table count |
| 2. One export at a time | Yes | `pg_advisory_xact_lock` in `requestExport`; test asserts `EXPORT_IN_PROGRESS` with the running job's id, and that company B is unaffected |
| 3. Soft-delete/cancel/purge shape | Yes | `deleteRequest`/`deleteCancel`/`deleteStatus`; test covers request→status→cancel→no-op purge→second cancel `NO_DELETION_PENDING` |
| 4. Hard purge purges rows + S3 | Yes | `hardPurgeCompany` deletes every `company_id` table in FK order plus S3 `deletePrefix`; test checks `headObject`/`listObjects` empty and company B's object/rows untouched |
| 5. Audited | Yes | one `audit()` call per action with correct `actorKind`; test asserts each |
| 6. 18-month buyer-PII retention | Yes | `redactStaleBuyerPii`/`buyerPiiCutoff`; test seeds an order at cutoff+1 day, asserts PII gone and totals/item counts intact |
| 7. `floor_requests` 30-day purge | Yes | `purgeOldFloorRequests`; test seeds old+recent rows for two companies, only the old one is deleted |
| 8. Cross-tenant safety | Yes | every export/purge/retention path filters by `company_id` inside `withTenant`/explicit `eq`; test asserts company B's rows, S3 object and audit log are untouched by every operation on A, and B gets `NOT_FOUND` (never `FORBIDDEN`) for A's job id and file key |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat`) — contracts: `contract/privacy.ts`, `roles.ts`, `schemas/{production,tenancy}.ts`, plus the granted-after-the-fact `contract.test.ts`/`roles.test.ts` hunks noted in the report. Backend: `modules/privacy/*`, `lib/s3.ts` (additive), `db/schema/tenancy.ts` (additive), `api/router.ts`/`modules/jobs.ts` (one line each), migration 0026, and the granted `files/service.ts` hunk (959a037).
- [x] Nothing outside scope — the Stripe-cancel and sign-in-during-soft-delete follow-ups are correctly left out and logged in the report/`wave.md`, not silently dropped.
- [x] Tests exercise the behavior, and none were weakened — scan output has no hits inside `privacy/` files; the `!env.isTest` scheduler guard mirrors the existing pattern in `worker/sweeps.ts`, not a new escape hatch.
- [x] Tenancy (`withTenant`, RLS on new tables), idempotency, money in cents, en/es text — no new UI text this card; money untouched. Idempotency verified live (advisory lock, jobId dedup on hard-purge, no-op re-run, no-op retention sweep on already-redacted orders).
- [x] Decisions recorded where needed — tombstone-vs-hard-delete of `companies` rationale is documented in the report (avoids cascading into other companies' `vendor_access` rows).

## Optional notes (not blocking)
- The known gaps in the report (sign-in during soft delete, Stripe cancel, Valkey/BullMQ leftovers on purge, users not globally deleted) are real but explicitly out of this card's scope per `wave.md`; the sign-in gap is flagged there as a P1 security follow-up, which is the right place for it.
