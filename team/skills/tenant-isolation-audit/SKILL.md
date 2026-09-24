---
name: tenant-isolation-audit
description: Audit InvAI's multi-tenant isolation end to end. RLS on every company_id table, policy shapes, app-role privileges, withSystem usage, S3 key checks, job tenancy, cache keys, cross-tenant NOT_FOUND tests and a live two-tenant probe. Use before a pilot or release, after a migration or new table, when reviewing tenancy-flagged cards, or when someone asks "can shop A see shop B's data".
---

# Tenant-isolation audit

With evidence, no request, job, file or cache path lets one company read or change another company's data, and
every known exception is written down and tested.

## When to use
- Before each release (`release-checklist`) and before any pilot goes live.
- A card adds a table, policy, migration, `withSystem` call, S3 key input, cache or job.
- As security-reviewer co-review for `tenancy` flags, or as the reviewer's deep check.
- After an incident that touched tenancy.

## Steps
1. **Run the isolation tests** (they use `invai_test`, not the dev DB):
   ```
   cd invai-backend
   pnpm test src/db/rls-coverage.test.ts src/db/rls.test.ts src/api/authz.test.ts \
     src/modules/tenancy/security.test.ts src/modules/channels/security.test.ts \
     src/modules/personalization/security.test.ts src/lib/security.test.ts
   ```
   All must pass. `rls-coverage.test.ts` fails on any `company_id` table without RLS; `authz.test.ts` walks
   every procedure (`listProcedures(contract)`) as anonymous, no-permission, floor, station-only and vendor.
2. **Run the database audit** against the local DB (read-only):
   ```
   docker exec -i local-postgres-1 psql -U invai -d invai -v ON_ERROR_STOP=1 < .claude/skills/tenant-isolation-audit/audit.sql
   ```
   Expected results, as of 2026-09-24:
   - §1 no rows; §3 no views without `security_invoker`; §4 no `SECURITY DEFINER` functions; §5 `f, f, 0`.
   - §2 lists only the reviewed exceptions: `gang_sheets_vendor_read/update`, `transfers_vendor_read`,
     `vendor_access_vendor_read`, `vendor_connections_vendor_read` (S-05, tested in `rls-coverage.test.ts`)
     and `plans`/`trademark_marks` public read. Anything new needs a test and an `EXPLAIN (ANALYZE, BUFFERS)`
     check at 1,000 tenants (research 11 §2.1).
   - §6 known non-tenant-leading indexes: the trigram indexes (research 11 G17, backlog B-37), unique keys
     (`files_key_unique`, `station_tokens_tokenHash_unique`, `channel_connections_connected_shop_uq`),
     vendor-side lookups, `outbox_events_pending_idx`, `buyer_pii_purge_after_index` (system jobs). A new
     entry needs a reason.
   - §7 and §8 print no `VISIBLE` or `CROSS-TENANT` notices.
3. **Review `withSystem` usage.** It is allowed only for the outbox relay, cross-tenant jobs, the seed, and
   the justified vendor and billing lookups (S-25).
   ```
   grep -rn "withSystem(" invai-backend/src --include=*.ts | grep -v "\.test\.ts"
   ```
   Each hit outside `src/worker/`, `src/db/seed/` and scheduled job fan-outs needs a reason comment on the
   line above. Cross-tenant jobs must read a list of ids as system, then do per-tenant work inside
   `withTenant`.
4. **Check client-supplied keys and ids.**
   - Every `*Key` input in the contracts is checked with `isCompanyKey()` (`src/lib/s3.ts`):
     ```
     grep -rnoE "[a-zA-Z]+Key: z\." invai-contracts/src | sort -u
     grep -rn "isCompanyKey(" invai-backend/src/modules
     ```
     Every key field in the first list must be checked in the service that receives it.
   - Foreign ids in inputs (location, blank variant, design, template) are loaded under the tenant before use,
     until composite FKs land (S-26, backlog B-30).
5. **Check jobs, events and caches.**
   - Job inputs carry `companyId` and handlers enter `withTenant`:
     `grep -rn "defineJob" invai-backend/src/modules` and read each handler.
   - A job never takes `companyId` from an unverified webhook body; webhooks match a `connected` connection
     first (S-04).
   - Cache and Valkey keys include the tenant (`c:{companyId}:…`, research 11 §6.3):
     `grep -rnE "redis\.(get|set|incr|expire|publish|subscribe)\(" invai-backend/src`.
   - Realtime channels are per company: read `src/lib/realtime.ts`.
6. **Probe the live API with two tenants.** On your own port (`PORT=31xx pnpm dev:api`), as the Desert Bloom
   owner, take an order id, a design file key and a gang sheet id. Then as a second shop (create one with
   sign-up, or use the golden-path step 13 helper in `invai-web/e2e/helpers/api.ts`), call the matching `get`,
   `update` and download procedures with those ids and keys. Every call must return `NOT_FOUND` (never
   `FORBIDDEN`, never data). Also try the vendor login (`vendor@suncitydtf.test`) against a sheet that wasn't
   shared with it.
7. **Check the golden-path isolation step** passed in the last `run-golden-path` (step 13), and that the floor
   and vendor portal are covered (research 12 §1.1 SHOULD).
8. **Record findings.** Each gap goes into `invai-docs/security/v1-review.md` (id `S-NN`, severity, area,
   description, status, owner) by the security-reviewer, with a failing test or curl as proof. Cross-tenant
   access is **High**: tell the owner immediately (`escalate-to-owner`, with Amazon's 24-hour clock) and start
   `incident-response` if real data could be involved.

## Rules
- MUST prove each finding with a failing test or a reproducible curl. No speculative findings.
- MUST NOT weaken or skip `rls-coverage.test.ts` or `authz.test.ts`, ever.
- MUST NOT run the audit against a non-local database without the owner's go-ahead (real data).
- MUST remember production differs: in AWS the app currently connects as the RDS master user, so RLS is not
  enforced there until backlog B-01 lands (research 11 G1). Any AWS audit starts by checking `DATABASE_URL`'s
  role.

## Done when
- Step 1 tests pass, with counts in the report.
- `audit.sql` output matches the expected results, or each difference is explained or filed.
- Every `withSystem` call and every `*Key` input is accounted for.
- The two-tenant probe returned `NOT_FOUND` for every foreign id and key tried (list them).
- Findings are in `security/v1-review.md` with owners, and Highs are escalated.

## References
- `audit.sql` (this folder)
- `invai-docs/research/12-security-quality-playbook.md` §1.1, §4 (tenancy checklist)
- `invai-docs/research/11-platform-scale-playbook.md` §2.1 (RLS performance), §6.3 (cache keys), G1, G17
- `invai-docs/security/v1-review.md` (S-04, S-05, S-11, S-12, S-25, S-26) and "What was verified"
- `invai-backend/src/db/client.ts` (`withTenant`, `withVendor`, `withSystem`), `src/db/schema/_shared.ts`
  (`tenantPolicy`)
