# T-12-4 report: tenant export, deletion and retention (B-23, without KMS)

Builder: backend-foundation, with compliance-officer input. Status: **built, not pushed**. It's ready for review by the security-reviewer (flags `pii` and `tenancy`).

## Commits
| Repo | SHA | What |
|---|---|---|
| invai-contracts | `13e7b14` | Stub B verbatim: `contract/privacy.ts` (5 procedures, `EXPORT_IN_PROGRESS`, `DELETION_ALREADY_REQUESTED`, `NO_DELETION_PENDING`). Adds `org.export` and `org.delete` (owner only, carved out of admin through `OWNER_ONLY` alongside `billing.manage`), Job kind `tenant_export`, and the four `tenant.*` audit actions. |
| invai-backend | `ba9db95` | `modules/privacy/{service,jobs,router,zip}.ts`, `tenant.test.ts`, migration `0026_tenant_soft_delete`, `lib/s3.ts` (`listObjects` and `deletePrefix`), `JOB_KINDS += tenant_export`, one line each in `api/router.ts` and `modules/jobs.ts`. |

## Design
- **Export.** `exportTrigger` runs in the tenant transaction. It takes `pg_advisory_xact_lock` on `tenant_export:{companyId}` and checks for a `queued` or `running` export. If one exists it throws `EXPORT_IN_PROGRESS {jobId, startedAt}`. Otherwise it creates the `jobs` row with `createJobRow` from production, writes the audit row, and enqueues after commit. If the enqueue fails, the row is marked failed so it can't block the next export.
  - The job `privacy.tenantExport` runs on the `reports` queue, 3 attempts, with jobId `tenant-export:{jobId}`.
  - It pages through every table that has `company_id`. The list comes from the Drizzle schema, so new tables are included automatically. Reads use `withTenant` plus an explicit `company_id` filter.
  - It writes `tables/<t>.json` and `tables/<t>.csv` for each table, adds the stored objects under `files/`, and writes a `manifest.json`. `raw/` payloads and earlier exports are skipped.
  - The zip is written to a temp file, entry by entry, and uploaded to `{companyId}/tenant-export/{jobId}.zip`. The job creates a `files` row (`kind: "export"`) whose **id is the job id**, and puts it in `jobs.resultIds`. A retry overwrites the same key and row.
  - Secret columns are excluded: `credentials`, `apiKey`, `inviteToken`, `tokenHash`, `pinHash`, `secret`.
  - CSV follows RFC 4180. Text that starts with `= + - @` gets a leading `'` so spreadsheets don't run it as a formula; the JSON files keep the exact values.
  - There is no zip library in the lockfile and `pnpm install` isn't allowed, so `zip.ts` is a small ZIP32 writer and reader built on `zlib`. The limit is 4 GiB or 65,535 entries; going over marks the job failed.
- **How the file is fetched.** `files.downloadUrl` takes a key, not an id, so the key is derived from the id. The contract comment on `privacy` documents the layout: `{companyId}/tenant-export/{fileId}.zip`.
- **Delete.** `deleteRequest` sets `companies.deletedAt` (only if it is null and the company isn't purged) and writes the audit row. After commit it schedules `privacy.tenantHardPurge` with jobId `hard-purge:{companyId}`, delayed 30 days. Any stale copy of that job is removed first, so BullMQ's jobId dedup can't swallow the new one.
  - `deleteCancel` clears `deletedAt` while `purgedAt` is null, audits, and removes the delayed job as a best effort. A copy that fires anyway is a no-op: it re-checks the company under `FOR UPDATE`.
- **Hard purge.** This is a `withSystem` job. Everything below happens in one transaction:
  - It checks the company is due (`deletedAt + 30 d`, with 1 minute of slack). If not, it returns `not_requested` or `not_due` instead of failing.
  - It deletes every `company_id` table, **children before parents**, in an order worked out from the Drizzle foreign keys.
  - In `audit_log` it deletes everything except the `tenant.*` lifecycle rows.
  - It deletes `members` and `invitations`, and clears `sessions.active_organization_id`.
  - It turns the `companies` row into an anonymized tombstone (`Deleted company`, `deleted-{id}`, `purgedAt`) and writes `tenant.purged` with actor `system`.

  After commit, `deletePrefix("{companyId}/")` deletes the objects in batches of 1,000. It refuses any prefix that isn't a single company's. A re-run finds the tombstone and repeats only the storage sweep.
  - I kept the tombstone on purpose. Deleting the `companies` row would cascade into **other** companies' `vendor_access` rows (their `vendor_company_id` has `ON DELETE cascade`) when the purged org is a vendor.
- **The append-only ledger.** On the real seed, the purge failed with `inventory_movements is append-only (DELETE not allowed)`.
  - Migration 0026 changes the trigger function so a DELETE passes only when `current_user <> 'invai_app'` **and** the row's company equals the transaction-local `app.purge_company_id`. Only the purge sets that value, on the owner connection.
  - A test proves the app role still can't delete ledger rows, even with the setting.
- **Retention.** The daily `privacy.retentionSweep` runs at 05:15 UTC on `reports`. It:
  - redacts buyer PII on orders placed more than 18 calendar months ago. It uses the same `redactOrders` as Shopify `customers/redact`: the `buyer_pii` row, the buyer note and ref, personalization answers and the raw payload object. Totals, items and dates stay. Each batch is audited as `privacy.redacted`.
  - deletes `floor_requests` older than 30 days.
  - re-enqueues any purge that is due but was lost.

  Company ids are read as system; the work runs per company inside `withTenant`.

## Acceptance criteria and evidence
Test file: `src/modules/privacy/tenant.test.ts`, 9 tests, all passing on its own DB `invai_test_t124`, which was migrated from scratch including 0026.
1. **Export trigger and status.** The test exports a company with 3 orders, runs the job inline, and gets status `done`. It downloads the zip through `files.downloadUrl` and a real `fetch`. `orders.csv` has 3 rows and `order_items.csv` has 6. The JSON ids match. Buyer PII is present, `credentials` is absent, and the file object is in the zip. The manifest covers every tenant table.
2. **Only one export at a time.** The second trigger fails with `EXPORT_IN_PROGRESS`, status 409, and `data {jobId, startedAt}` equal to the first job's. Company B isn't blocked. After the first finishes, a new trigger works.
3. **Soft delete, cancel and a no-op purge.** `scheduledPurgeAt` is within 60 s of now + 30 d, `deleteStatus` shows `soft_deleted`, and the BullMQ job is in the `delayed` state. A second request gets `DELETION_ALREADY_REQUESTED`. After cancel, the status is `active`, the job is gone, and an inline purge returns `{purged:false, reason:"not_requested"}` with the data intact. A second cancel gets `NO_DELETION_PENDING`. A purge that fires early returns `not_due`.
4. **Hard purge.** After fast-forwarding and running inline, **every** `company_id` table is empty for A except `audit_log` (2 `tenant.*` rows). The tombstone and member removal are checked. `HeadObject` on the file returns `exists: false` and listing the prefix returns nothing. A second run gives `alreadyPurged: true, objects: 0`.
5. **Audited.** There is one assertion per action. `export_requested`, `delete_requested` and `delete_cancelled` carry `actorKind: user` and the owner's id. `purged` carries `actorKind: system` and a null user.
6. **18-month buyer PII.** An order placed 18 months + 1 day ago loses `buyer_pii`, the note, the ref and the personalization answers. `totalCents`, `subtotalCents`, `itemCount`, `placedAt`, `orderNo` and the item count are unchanged. A recent order and company B's order are untouched. A second sweep writes no second audit row.
7. **`floor_requests`.** Only the row older than 31 days is deleted; recent rows are kept for both companies.
8. **Cross-tenant.** Every test uses a second real company on the RLS database and checks its rows (orders, items, PII, files, audit, ledger), its S3 object and its audit count before and after. It also checks that B gets `NOT_FOUND` for A's export key through `files.downloadUrl` and for A's job through `exportStatus`, and that the zip holds no id of B's. Admin gets `FORBIDDEN` on `exportTrigger` and `deleteRequest`, and the generic `authz.test.ts` covers the new procedures.

Other checks:
- Related suites pass, 78 tests: `privacy/*`, `rls-coverage`, `rls`, `authz`, `migrate`, `inventory/*`, `files/*`, `orpc`, `job-failures`, `internal`, `lib/security`.
- Typecheck is clean in backend, web and floor. Biome is clean. Contracts: 31/31 tests pass.

**Real run on a scratch copy of the dev DB** (`pg_dump` into `invai_t124_scratch`, migrated to 0026, since dropped):
- **Export of Desert Bloom** through `call(router.privacy.*)` and `files.downloadUrl`: `done` in 974 ms, a 42.7 MB zip with 221 entries (59 tables and 102 files). `orders.csv` has 360 rows, matching 360 in the DB. The zip object was deleted afterwards, because the scratch DB shares MinIO with dev.
- **Deletion** on a new company in the scratch DB: `deleteRequest` then `deleteStatus` showed `soft_deleted` with `scheduledPurgeAt` 2026-10-26. After fast-forwarding, the purge returned `purged: true, objects: 1`, `HeadObject` returned false and the listing was empty. The seeded orders were untouched.
- **Full purge of the seeded Desert Bloom rows** on the scratch DB, pointed at a throwaway bucket `invai-t124-scratch` so no dev files were touched: 18,528 rows across 41 tables deleted in 85 ms. Afterwards only `audit_log: 2` remained. This is the run that found the ledger trigger problem.

## Out-of-owned-path edits (please grant after the fact)
- `invai-contracts/src/contract.test.ts`: added `jobId` to the list of allowed GET path parameters. Stub B's exact path `/export/{jobId}` needs it. The test isn't weakened.
- `invai-contracts/src/roles.test.ts`: one added assertion that only the owner holds `org.export` and `org.delete`.
- `invai-contracts/src/schemas/production.ts` (`Job.kind += tenant_export`) and `schemas/tenancy.ts` (`AUDIT_ACTIONS`): both are required by stub B.
- `invai-backend/src/modules/jobs.ts`: one import line, the documented way to register a module's jobs.
- The migration 0026 trigger change described above (schema change and migration in the same commit).

## Known gaps and follow-ups
1. **Fixed in `959a037` (granted):** `KIND_PERMISSIONS` now has `"tenant-export": ["org.export"]`. A test checks that presser, office, designer and admin get `NOT_FOUND` on an export key while the owner can download it. Only this hunk was staged; T-12-5's edits in the same file were left alone. The original note follows. **Export key readable with `files.read`.** `files/service.ts` `KIND_PERMISSIONS` doesn't restrict the `tenant-export` key segment. Anyone in the same company with `files.read` who *knows the key* could download the export; that includes pressers. Keys contain a random UUID and aren't listed anywhere a presser can reach. The only way to learn one is the job id, via `privacy.exportStatus` (owner only) or `production.jobs.get` (needs the id). The one-line fix is `"tenant-export": ["org.export"]` in `KIND_PERMISSIONS`. T-12-5 currently has uncommitted edits in that file, so I left it alone.
2. **Stripe isn't cancelled on delete.** Billing rows are purged, but a live Stripe subscription would keep charging. `deleteRequest` or the purge should call billing's cancel, which is owned by the billing track.
3. **A soft delete is only a flag.** It doesn't block sign-in or stop imports or syncs during the 30 days, and the web has no screen for it. Web and floor UI are out of this card's scope.
4. **Users aren't deleted.** Global Better Auth `users` who were only members of the purged company keep their accounts (InvAI is the controller for those). This needs an owner or compliance decision.
5. **Leftovers outside Postgres and S3.** Valkey keys (`c:{companyId}:*`, the rate limiter and semaphores) and in-flight BullMQ job data for the company aren't swept; they expire on their own TTLs. Database backups age out on the RDS retention window, which the privacy playbook says to state in the reply.
6. **Scale limits.** The export holds one table page (5,000 rows) and one object in memory, but builds each table's CSV and JSON in memory, and it is ZIP32. Very large tenants (over 4 GiB, or tables with millions of rows) need ZIP64 and streaming, as a backlog item. The purge is one transaction per company; at seed size it takes 85 ms.
7. `invai-docs/compliance/privacy-requests/log.md` was not touched, because no real request was handled.

## Cleanup
- Dropped `invai_test_t124` and `invai_t124_scratch`.
- Flushed Valkey db 9, which I used for all runs.
- Deleted the temporary bucket `invai-t124-scratch` and the scratch export object.
- Removed the temporary scripts. I started no long-running processes.
