---
name: add-backend-feature
description: Build a backend feature inside one invai-backend domain module - router, service, jobs, outbox and realtime events, errors, tests against invai_test with RLS, and curl as the right role on your own port. Use for "implement procedure", "fill the stub", "backend feature", "service function" or work in src/modules/<area>.
---

# Add a backend feature

A feature that follows the module patterns exactly, runs inside the tenant, is tested against the real test
database and is proven with curl as the role that will use it.

## When to use
- A card assigns you `invai-backend/src/modules/<area>/**` (backend-engineer), and the contract procedure
  exists (it may be a `stubRouter` stub).
- Not for `src/ai/**` (`ai-feature-with-evals`), `src/integrations/**` or `src/api/webhooks.ts`
  (`add-marketplace-integration`), or core `src/{db,lib,api,worker,test}` (backend-foundation).
- Missing procedure? Stop and ask the tech lead for an architect change (`add-contract-procedure`). Never add
  an off-contract endpoint.

## Steps
1. **Read** `src/modules/README.md`, the catalog module (`router.ts`, `service.ts`, `jobs.ts`,
   `service.test.ts`), your module, and the procedure in `invai-contracts/src/contract/<domain>.ts` with its
   schemas.
2. **Service first** (`service.ts`): public functions `(tx: Tx, ctx: TenantContext, input) => output`.
   - Lists: `keyset(table.createdAt, table.id, input)` from `src/lib/pagination.ts`, fetch `limit + 1`,
     `page.result(rows, toX)`. Max page size 200.
   - Map rows in a `toX()` function; the contract's output schema is the truth (ISO strings, cents, inches).
   - Foreign ids from input: load them under the tenant first; a miss is `notFound()` (S-26: FKs don't check
     the tenant).
   - Other modules' data only through their `service.ts` exports (list in
     `.claude/agents/backend-engineer.md`, "Cross-module functions").
   - Item state changes only through `transitionItem(tx, itemId, to, { actor, ... })` in
     `modules/orders/state-machine.ts`.
3. **Same-transaction side effects:** `audit(tx, {...})` for what a person did (`src/lib/audit.ts`); `emit(tx, companyId, "event.name", payload)` for what a worker reacts to (`src/lib/outbox.ts`, ids only in the
   payload); `afterCommit(tx, () => publish(companyId, {...}))` for realtime (`src/lib/realtime.ts`).
4. **Errors** from `src/lib/errors.ts` (`notFound`, `conflict`, `invalidTransition`, `planLimit`, `upstream`,
   `rateLimited`, `badRequest`). Cross-tenant access returns `NOT_FOUND`, never `FORBIDDEN`. Scans and other
   business outcomes return results.
5. **Router** (`router.ts`): one line per handler:
   ```ts
   hold: authed.orders.hold.handler(({ input, context: { tenant } }) =>
     withTenant(tenant.companyId, (tx) => svc.holdOrder(tx, tenant, input))),
   ```
   Remove the procedure from the `stubRouter(...)` spread once implemented. Vendor-portal handlers use
   `withVendor`. The guard already enforced auth and permission from the contract meta; don't re-check roles
   by name.
6. **Heavy or outward work goes to a job** (`jobs.ts`, `defineJob` + `onEvent`), following `idempotent-job`;
   money or marketplace calls also follow `idempotent-side-effect`. Bulk endpoints check quotas
   (`assertWithinPlan` in `modules/billing`) and size limits.
7. **Plan limits and usage:** call billing's `assertWithinPlan` / `recordUsage` where the card says a meter
   applies.
8. **Tests** in `src/modules/<area>/*.test.ts` against `invai_test` (RLS on), using `src/test/fixtures.ts`
   (`createCompany`, `createUser`, `tenantContext`, `createConnection`, `createOrder`):
   - happy path;
   - idempotent retry (call twice, one effect);
   - cross-tenant: company B with A's id gets `NOT_FOUND`;
   - each edge case on the card;
   - router-level where auth matters: `call(router.<ns>.<proc>, input, { context })` from `@orpc/server`.
   Run: `pnpm typecheck && pnpm lint && pnpm test` (or `pnpm vitest run src/modules/<area>` while iterating).
9. **Exercise it for real** on your own port, as the role that will use it (see "Curl as a role" below). Watch
   the worker log for your job and check the DB row changed once.
10. **Report** (`verify-and-report`): commands and output, functions other modules may now call, anything left
    on `stubRouter`.

## Curl as a role
```
export PATH="$HOME/.local/share/pnpm/bin:$HOME/.local/share/pnpm:$PATH"
cd invai-backend && PORT=3107 pnpm dev:api          # your own port; 3000 may be another agent's
J=/tmp/invai-office.jar; O="origin: http://localhost:5173"
curl -s -c $J -H "$O" -H 'content-type: application/json' \
  -d '{"email":"office@desertbloom.test","password":"demo1234!"}' http://localhost:3107/api/auth/sign-in/email
curl -s -b $J -H "$O" "http://localhost:3107/api/v1/<prefix>/<path>"          # REST path = contract prefix + route path
```
Also try a role that must be refused (for example `presser@`) and expect 403, and the vendor login
`vendor@suncitydtf.test` for portal work. `tsx watch` restarts when other agents edit files: retry a request
that died mid-restart. Stop your API when done.

## Rules (MUST / MUST NOT)
- MUST run every request-scoped query in `withTenant`; `withSystem` only with a written reason in code.
- MUST insert `companyId` explicitly on every tenant row.
- MUST NOT query or write another module's tables.
- MUST NOT log PII; use `logger("<area>")`, never `console.*`.
- MUST put timeouts on every external call and keep indexes `company_id`-first.
- MUST add a migration only when existing tables can't hold the data (`add-tenant-table`,
  `zero-downtime-migration`), with backend-foundation as co-reviewer.

## Done when
- The procedure is off `stubRouter`, and `pnpm typecheck && pnpm lint && pnpm test` pass.
- Happy-path, retry and cross-tenant tests exist.
- Curl output as the right role (and a refused role) is in the report; jobs and realtime events were seen
  firing.
- For a golden-path area: `E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts` in `invai-web` passes on a fresh
  seed.

## References
- `invai-backend/src/modules/README.md`, `src/modules/catalog/**`, `src/test/fixtures.ts`
- `invai-docs/research/11-platform-scale-playbook.md` §9 (backend checklist);
  `12-security-quality-playbook.md` §4
- Related: `add-contract-procedure`, `idempotent-job`, `idempotent-side-effect`, `add-tenant-table`,
  `root-cause-bug`
