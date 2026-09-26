# Review of T-12-4 (round 1)

- Reviewer: security-reviewer on Sonnet 5
- Author: backend-foundation on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git show 13e7b14` (roles.ts, roles.test.ts) | `org.export`/`org.delete` in `OWNER_ONLY`, carved out of `admin`'s `SHOP_ALL` the same way as `billing.manage`; `roles.test.ts` asserts no non-owner role has either permission |
| `git show ba9db95` (`lib/s3.ts` `deletePrefix`) | regex `^[0-9a-f-]{36}/$` refuses anything but one whole company UUID prefix |
| `git show ba9db95` (migration 0026 trigger) | `inventory_movements_append_only()`: DELETE only passes when `current_user <> 'invai_app'` **and** `OLD.company_id` matches the transaction-local `app.purge_company_id` |
| `grep -n withSystem src/db/client.ts` | confirms `withSystem` runs on the "owner connection, no RLS" (`systemDb`), a different Postgres role than `invai_app` used by `withTenant`/the app |
| `NODE_ENV=test pnpm db:migrate` against a scratch DB (`invai_review_t124`), then `vitest run src/modules/privacy/tenant.test.ts` | 10/10 passed, incl. the ledger-abuse test at tenant.test.ts:404-412 (app role sets `app.purge_company_id` itself and still gets rejected on DELETE) |
| `vitest run src/db/rls-coverage.test.ts src/db/rls.test.ts src/api/authz.test.ts` | 20/20 passed |
| `git show 959a037 -- src/modules/files/service.ts` | `KIND_PERMISSIONS["tenant-export"] = ["org.export"]`; kind is derived from the key's second path segment (`{companyId}/tenant-export/{fileId}.zip`), which matches how the export is keyed |
| Read `tenant.test.ts` cross-tenant assertions (lines ~190-282, ~380-415) | company B's rows/S3 object/audit untouched by every A operation; B gets `NOT_FOUND` (never `FORBIDDEN`) for A's export key and job id |
| `bash .claude/skills/independent-review/scan-test-weakening.sh invai-backend origin/main` | no hits inside `modules/privacy/*` |
| Dropped `invai_review_t124` after | cleaned up |

## Threat-model checklist (card's explicit items)
| Item | Verdict | Evidence |
|---|---|---|
| Export and delete are owner-only | Pass | `org.export`/`org.delete` in `OWNER_ONLY`; test: admin gets `FORBIDDEN` on both `exportTrigger` and `deleteRequest` |
| Export contains only this company's data | Pass | `exportRows` runs `withTenant(companyId, ...)` plus an explicit `eq(t.companyId, companyId)` filter (belt-and-suspenders with RLS); stored files use `listObjects(prefix)` scoped to `{companyId}/`; test asserts company B's id and order ids never appear in A's zip bytes |
| Export file download needs `org.export` | Pass | `files/service.ts` `KIND_PERMISSIONS["tenant-export"]`; test: presser/office/designer/admin (all `files.read` holders) get `NOT_FOUND`, owner gets the file |
| Migration 0026: owner-only ledger delete can't be abused by the app role | Pass | trigger requires `current_user <> 'invai_app'`; this is unconditional — even if the app role could set the transaction-local GUC (which any role can), the `current_user` check alone blocks it. Confirmed `withSystem`/purge runs as a different DB role than `withTenant` |
| S3 purge covers only this company's prefix | Pass | `deletePrefix` regex refuses any prefix that isn't exactly one company UUID; test confirms B's object survives A's purge |
| Retention job (18 months buyer PII) | Pass | `redactStaleBuyerPii`/`buyerPiiCutoff`; reuses the same `redactOrders` path as the existing Shopify `customers/redact` handler, so it's consistent with the already-reviewed redaction logic |
| Idempotency (export in progress, deletion already requested) | Pass | `pg_advisory_xact_lock` serializes concurrent `exportTrigger`s → `EXPORT_IN_PROGRESS`; `requestDeletion`'s `WHERE isNull(deletedAt)` guard → `DELETION_ALREADY_REQUESTED`; hard-purge jobId `hard-purge:{companyId}` dedups, and a stale delayed job that fires anyway re-checks the company and no-ops |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened
- [x] Tenancy (`withTenant`, RLS on new tables), idempotency, money in cents, en/es text — no new tenant tables; `companies.deletedAt`/`purgedAt` are plain columns on an existing RLS-covered table
- [x] Decisions recorded where needed

## Optional notes (not blocking)
- The report's follow-up #1 ("soft delete doesn't block sign-in for 30 days") is flagged in `wave.md` as a P1 security follow-up, correctly not folded into this card. I checked it isn't silently dangerous in the interim: a soft-deleted company's data isn't purged or exposed to other tenants during those 30 days, it's just still reachable by its own users — acceptable as a tracked gap, not a blocker here.
- Valkey/BullMQ leftovers (rate-limiter and semaphore keys, in-flight job data) aging out on their own TTL rather than being swept on purge is a minor residual-data gap, already logged by the author as a known follow-up. Not blocking — no cross-tenant exposure, just slower-than-ideal deletion of ephemeral operational state.
