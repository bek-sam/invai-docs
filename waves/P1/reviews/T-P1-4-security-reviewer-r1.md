# Security review of T-P1-4 (round 1)

- Reviewer: security-reviewer on Sonnet 5
- Author: backend-engineer (catalog) on Opus 5.5
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm test src/db src/modules/catalog src/integrations/imaging --reporter=dot` (own test DB, global-setup) | 15 files, 55 passed, 0 failed. Includes `src/db/rls-coverage.test.ts`, `src/db/rls.test.ts`, `catalog/jobs.test.ts`, `catalog/service.test.ts`, `imaging/client.test.ts` |
| Read `git show 7247b32` in full (client.ts, jobs.ts, service.ts, mapping.ts, builder.ts, tests) | matches the report |
| Read `src/modules/files/service.ts` `downloadUrl`/`canReadKind` (pre-existing, not touched) | preview key's `kind` segment ("preview") isn't in `KIND_PERMISSIONS`, so it defaults to allow like "design" — same role-check regime as other catalog keys, no regression |

## AC7 and the imaging trust model (my T-P1-2 note: imaging trusts the backend for company prefixes)
- **Job path**: `service.ts` `renderDesignPreviews()` calls `isCompanyKey(ctx.companyId, file.fileKey)` and `isCompanyKey(ctx.companyId, outKey)` before every `imaging.preview` call, `BAD_REQUEST` otherwise. Proven by `service.test.ts` with a row whose `fileKey` was forced outside the tenant. Job (`jobs.ts`) runs the whole thing inside `withTenant(companyId, …)`; mismatched `{companyId, designId}` returns `NOT_FOUND` via RLS (tested in `jobs.test.ts`). Payload can't be used to name another company's file.
- **Retry**: `jobId: design-preview-${designId}` dedupes retries onto the same checked handler; `designPreviewKey()` is deterministic so a rerun overwrites the same object (one row, same key — tested).
- **Seed path**: `builder.ts` calls `imaging.preview` directly, **not** through `renderDesignPreviews()`, so it skips the explicit `isCompanyKey` call — literally short of AC7's "before every `imaging.preview` call." I checked whether this is exploitable: `fileKey` is the design file row just created by `createDesign()`, which itself enforces `isCompanyKey(ctx.companyId, p.fileKey)` at line 202 before insert; `out_key` is `designPreviewKey(shopId, file.id)`, built directly from the same `shopId` the seed is already operating under. Both keys are therefore provably inside the tenant by construction, and `shopId` is never attacker- or request-controlled in the seed. **Not a security gap in practice** — no cross-tenant read/write is reachable — but it is a drift from the single enforcement point, and a future refactor that copies this seed pattern into a request path would lose the check. Non-blocking; suggest the seed call `renderDesignPreviews()` instead for consistency (owner: backend-engineer/catalog, hardening, Low).

## Other review-brief points
- `out_key` is **not** built from the existing `objectKey()` helper; the author added a new deterministic `designPreviewKey(companyId, designFileId)`. Justified: `objectKey()` mints a fresh random UUID per call, which would break AC1's idempotency (one object per file, not one per run). The new helper is still `${companyId}/…` and is checked by `isCompanyKey` before use. No weakening — a deliberate, reasonable substitution, not a different security boundary.
- Preview download: served only through the existing `files.downloadUrl` (unchanged in this diff), same prefix-ownership and `canReadKind` checks as every other kind. Author showed `presser@` refused `FORBIDDEN` at `catalog.designs.list` (the actual gate, since pressers can't list designs to learn preview keys) and `designer@` successfully downloading a real PNG. Consistent with the existing role-check regime; no new exposure.
- Placeholder/mock path: `client.ts`'s catch-all writes `placeholderPreviewPng()` to `out_key` as given. For the job path `out_key` was already `isCompanyKey`-checked by the caller before the client call; for the seed path it's safe by construction (see above). The client itself does not check company prefixes — consistent with the established model (enforcement lives in the caller, not imaging/the client).
- Tenant isolation (AC6) and the refusal test (AC7) both pass and are proven by failing-without-change-style tests (new `jobs.test.ts`/`service.test.ts` cases import/exercise code that doesn't exist on the prior commit).

## Blocking findings
None.

## Checks
- [x] RLS/authz-adjacent suites green: `rls-coverage.test.ts`, `rls.test.ts` pass with this diff.
- [x] `withTenant` used throughout the new job/service path; no new `withSystem`.
- [x] Every *new* `imaging.preview` call site I found (job→service, seed) was reviewed for tenant safety; only the seed skips the explicit check, and it's safe by construction (see above, logged as a Low hardening note, not a finding requiring an owner clock).
- [x] No PII involved (design files/previews, not buyer data).

## PIDs
None started. The test run was a self-contained `pnpm test` against its own global-setup DB; no API/worker/imaging process was launched by me.
