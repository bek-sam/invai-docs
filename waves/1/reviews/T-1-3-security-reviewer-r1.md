# Review of T-1-3 (round 1)

- Reviewer: security-reviewer on Opus
- Author: integrations-engineer on Opus 5.5
- Verdict: **approve**

## Evidence I re-ran
Same clean worktree at `b117997` (parent `293047b`), own DB `invai_test_r13`.

| Command | Result |
|---|---|
| `pnpm test src/db/rls-coverage.test.ts src/db/rls.test.ts src/api/authz.test.ts` | `3 passed (3)`, `20 passed (20)` — `rls-coverage.test.ts` (fails on any `company_id` table missing RLS) is green with the new `purchase_order_receipts` table present |
| `docker exec -i local-postgres-1 psql -U invai -d invai_test_r13 -c "\d+ purchase_order_receipts"` | `company_id uuid not null`, row security enabled, policy `purchase_order_receipts_tenant` present |
| `docker exec -i local-postgres-1 psql -U invai -d invai_test_r13 -c "select polname, qual, with_check from pg_policies where tablename='purchase_order_receipts'"` | `purchase_order_receipts_tenant`, `USING`/`WITH CHECK` both `company_id = nullif(current_setting('app.company_id', true), '')::uuid` — matches `tenantPolicy()`'s standard shape |
| `grep -rn "withSystem(" src/integrations/suppliers src/modules/inventory --include=*.ts \| grep -v test` | no hits — no new `withSystem` in the diff |
| `grep -rnoE "[a-zA-Z]+Key: z\." invai-contracts/src \| grep -i idempot` and `grep -rn "isCompanyKey" src/modules/inventory` | `idempotencyKey` is a client-supplied opaque string used only as a dedupe key (never a file/S3 key), scoped to `(company_id, key)` — `isCompanyKey()` doesn't apply here, correctly not used |
| `pnpm test` (full) | `212 passed (212)` |

## Acceptance criteria (security angle)
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | No platform credentials (`SS_ACTIVEWEAR_*`) reachable from tenant-triggered code anymore — `getSupplierAdapter`/`supplierProvider` take only `companyCreds`; a `grep -n "env.SS_ACTIVEWEAR" src/integrations src/modules` in the diff returns nothing. This closes the actual tenant-isolation gap: before this change, one company's PO could have shipped on InvAI's own S&S account (a billing/liability leak across tenants), and any tenant without credentials would silently ride InvAI's account in production. |
| Tenancy | yes | New table `purchase_order_receipts`: `company_id` not null, `tenantPolicy()` + `.enableRLS()`, both indexes lead with `company_id`. FK to `purchase_orders`/`locations` don't cross tenants (both already tenant-scoped tables). |
| PII | n/a | No buyer PII touched by this table or these files. |

## Blocking findings
None from a security standpoint (cross-tenant access, auth bypass, PII leak). I concur with `reviewer`'s and `architect`'s blocking finding on the SanMar/"other" silent-`submitted` behavior, but that is a business-correctness/contract-semantics issue, not a tenancy, auth or PII control weakening — I'm not duplicating it as my own blocking finding, since neither control I own (RLS, the authz/procedure matrix) is affected. The card cannot ship until their blocking finding clears regardless of my verdict.

## Checks
- [x] RLS on new table + tenant-leading indexes.
- [x] No new `withSystem`.
- [x] No client-supplied key used to reach another tenant's files/rows.
- [x] `authz.test.ts`/`rls-coverage.test.ts` green.
- [x] No PII involved.

## Optional notes (not blocking)
- Worth a follow-up: once `submit_attempted_at`-based in-flight detection has been live a while, confirm the 2-minute `SUBMIT_IN_FLIGHT_MS` window can't be used for a cheap DoS (a company hammering `submit` on its own PO just gets `CONFLICT`s on its own data — no cross-tenant exposure, low priority).
- Concur with `reviewer`'s note on the SanMar/"other" `submitted`-with-no-call path: if kept, the missing supplier confirmation should be a typed signal, not only an audit string, so a future permission/report built on `purchase_orders.status` doesn't misread "submitted" as "sent."
