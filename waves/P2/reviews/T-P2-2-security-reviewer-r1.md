# Security co-review of T-P2-2 (round 1, `files` flag)

- Reviewer: security-reviewer on Sonnet 5
- Author: backend-engineer (catalog) on Opus 5.5
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm test src/modules/catalog src/db --reporter=dot` | 14 files, 50 tests passed, 0 failed |
| Read `git show f6002ff 79906a5` in full (client.ts, jobs.ts, service.ts, router.ts, tests) | matches the report and reviewer r1's findings/fix |
| `grep -n isPermanentHttpStatus src/lib/queues.ts` | existing export, only imported — `lib/queues.ts` not edited (outside owned paths, correctly untouched) |

## Focus points
1. **`isCompanyKey` on both keys, every call** — `service.ts` `renderDesignPreviews()` still checks `isCompanyKey(companyId, file.fileKey) || isCompanyKey(companyId, outKey)` immediately before each `imaging.preview()` call, unchanged in spirit from T-P1-4 (now using the explicit `companyId` parameter instead of `ctx.companyId`; both are the same value — `ctx = systemContext(companyId)` in `jobs.ts`). Proven by `service.test.ts:228` ("refuses to preview a key outside the tenant … B-209 AC7"), still passing.
2. **Tenant context not lost between read and write transactions** — the read (`withTenant(companyId, select…)`), the imaging call (no transaction), and each per-file write (`withTenant(companyId, update…)`) all thread the same explicit `companyId` parameter rather than relying on one ambient open transaction. That `companyId` originates from the job's queued input (`{companyId, designId}`), itself set when the design event was emitted inside the original tenant's `withTenant`. No point drops or substitutes the tenant.
3. **Write transactions under `withTenant`, not `withSystem`** — confirmed: all three `withTenant(companyId, …)` calls in `renderDesignPreviews`; `grep -n withSystem` finds none added. RLS applies to every read and write.
4. **`file_key` guard can't cross tenants** — the write is `UPDATE designFiles SET previewKey=… WHERE id=? AND fileKey=?`, executed inside `withTenant(companyId, …)`. The `fileKey` equality guard is a race-condition guard (stale render after a replace), not a tenant boundary; RLS is what actually restricts the row set to this `company_id`, so even a crafted or stale `file.id`/`fileKey` pair can't touch another tenant's row — RLS would return zero rows before the `fileKey` predicate matters. Defense in depth, no gap.
5. **Duration logs carry no PII/file keys** — `router.ts` `scan` logs only `{companyId, stationId, durationMs}`; `jobs.ts` render job logs only `{companyId, designId, durationMs, imagingMs}`. Verified live in the test run above (stdout lines show exactly these fields, no file keys, no buyer data). Matches AC4.
6. **T-P1-4 AC6/AC7 still pass** — `service.test.ts:228` (AC7, key-outside-tenant refusal) and `service.test.ts:271` ("can't render or read another company's design … tenant isolation", AC6) are both present and green; `jobs.test.ts:89-111` keeps the job-level cross-tenant `NOT_FOUND` test (company A's job id against company B's design).

## Round-1 reviewer findings (1–3), re-checked for security impact
- Finding 1 (placeholder masking a real outage) was a resilience/staleness bug, not a tenancy or auth issue; the round-2 fix (`allowPlaceholder: false` for the job path) doesn't touch the tenant or key checks. No new exposure introduced by the fix.
- Findings 2–3 (missing replace-clears test, job test not exercising the real client) are test-coverage gaps, not security gaps; both closed in `79906a5` with no weakening of existing assertions (confirmed by reading the diff — only additive tests and a new `allowPlaceholder` option).

## Blocking findings
None.

## Checks
- [x] `isCompanyKey` on `file_key` and `out_key` before every `imaging.preview()` call (service.ts)
- [x] Tenant context (`companyId`) explicit and unbroken across the read tx → imaging call → write tx
- [x] `withTenant` only; no `withSystem` added
- [x] `file_key` guard backed by RLS, not a substitute for it — can't write across tenants
- [x] New duration logs: no PII, no file/object keys, only ids and ms
- [x] T-P1-4 AC6 (job-level cross-tenant NOT_FOUND) and AC7 (key-outside-tenant refusal) tests present and green

## PIDs
None started. Test run was self-contained (`pnpm test`, own `invai_test` DB via global-setup); no API/worker/imaging process launched by me.
