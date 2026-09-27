---
name: sample-workspace-and-global-tables
description: How "sample workspace" is really defined (not companies.demo) and how global no-company_id tables are written safely (withSystem = owner connection); learned reviewing the wave 18 plan
metadata:
  type: project
---

- `companies.demo` is NOT the sample-workspace test. A sample workspace is `isSampleWorkspace(companyId)` in `invai-backend/src/modules/tenancy/demo-flag.ts` (`demoOwnerUserId` set or `settings.demoRetiredAt`). The seeded Desert Bloom shop has `demo = true` and gets real behavior. Plans and ADRs that say "demo" for mock selection are wrong until they say `isSampleWorkspace`.
- Mock visibility rule agreed for market signals (wave 18): mocks are used/shown when `!env.isProd || env.allowMocks || isSampleWorkspace(companyId)`; a per-company rule must live in the consuming module, not in provider selection, whenever the refresh is global.
- Global tables without `company_id` (`plans`, `trademark_marks`, `market_series_cache`): `publicReadPolicy` + `.enableRLS()` makes the app role select-only; writes go through `withSystem` (the owner connection, `db/client.ts`), same as `db/reference/index.ts`. Each needs two edits in security-reviewer's `rls-coverage.test.ts`: `PUBLIC_READ_TABLES` and the "cannot write the global catalogs" array.
- `contract.test.ts` forces `cursor`/`nextCursor` on every procedure whose path ends in `.list` (plus inbox/ledger/queue/...); plan a `paginated()` output or an explicit exemption before agreeing an interface that returns an array.

**Why:** the wave 18 plan used `companies.demo` and an array-returning `recommendations.list`; both would have failed at build time.
**How to apply:** check these four points in every plan review that adds a mock-backed provider, a global table or a `.list` procedure.
