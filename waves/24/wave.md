# Wave 24: deployable without an AWS account (roadmap wave 10, agent part)

- Dates: planned; can start in parallel with wave 22/23 cards that don't touch `invai-infra` or the backend build (at most 3 builders at once overall)
- Goal (user outcome): the owner's first staging deploy is a short checklist. `sst.config.ts` synthesizes with no known deploy-time failure, every image builds and runs as non-root, migrations and reference data run as a one-off task as the right DB users, and every secret, domain and account step the owner must do is an exact OI checklist.
- **Hard fence:** no `sst deploy`, no `aws`, no secrets set, no accounts, no spend. The guard blocks these. Checks are `tsc`, `sst` config type checks without credentials if possible, `docker build`, local `docker run`, and compose.
- Sources (backlog): B-01, B-02, B-03, B-23 (KMS part: provider interface, local fallback), B-57, B-58, B-59, B-73, B-74, B-77, B-163 (if not done in wave 22), B-107 (AWS parts: WAF, S3 gateway endpoint, ARM), wave 9 deferrals (`IMAGING_SHARED_SECRET` to all services, ECS `stopTimeout` ≥ 35 s, compose `full` profile flags).
- Plan reviewed by: product-manager (2026-09-28, approve), architect (2026-09-28, approve with change A1: entry points named above). Security co-reviews every platform-sre card.

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| T-24-1 SST config fixes: imaging service URL, worker env, stage URLs, one domain + ACM, HTTPS listener, Valkey `noeviction` cluster-off, RDS production settings, S3 lifecycle/CORS/versioning, secrets list, KMS key, WAF, S3 gateway endpoint, ARM, `stopTimeout` (B-02, B-03 HTTPS, B-57, B-73, B-74, B-77, B-107) | platform-sre | opus | reviewer (sonnet) + security-reviewer | security | planned |
| T-24-2 Backend production build: compiled migrate + bootstrap (`invai_app`, proxy secret) + reference-seed entry points, `drizzle/` in the image, SMTP/SES env schema, KMS field-encryption provider behind an interface (B-01, B-58 env, B-59, B-23 KMS) | backend-foundation | fable | reviewer (opus) + security-reviewer | auth, pii, migration | planned |
| T-24-3 Dockerfiles and compose: multi-stage, non-root, pinned by digest, HEALTHCHECK, root `.dockerignore`, compose `full` profile that runs the built images end to end locally (B-21 images, B-76 compose) | platform-sre | sonnet | reviewer (opus) + security-reviewer | security | planned |
| T-24-4 Deploy runbook and the owner's go-live checklists (OI entries with exact steps: AWS account and SSO, GitHub OIDC role, region, domain + Route 53, `sst secret set` per stage, SES production access + DKIM/SPF/DMARC, first staging deploy, smoke test, rollback) | docs-writer | sonnet | platform-sre (domain) + security-reviewer | — | planned |

## Agreed interfaces (architect A1)
- Built entry points in the backend image (T-24-2 provides, T-24-1 and T-24-3 consume): `node dist/db/bootstrap-cli.js` (creates/updates `invai_app` and its password from a secret; idempotent), `node dist/db/migrate-cli.js` (advisory-locked migrations only), `node dist/db/reference-seed-cli.js` (plans, trademark marks; idempotent), `node dist/api/server.js`, `node dist/worker/index.js`. `drizzle/` is copied to `/app/drizzle`. The one-off ECS task runs the three CLIs in that order.

## Order
- T-24-2 and T-24-3 first (images), T-24-1 in parallel (config only), T-24-4 last (it documents what the others built).

## Integration gate
- [ ] `docker build` of api/worker, imaging, web, floor images; `docker compose --profile full up` runs the golden path against the built images (`E2E_API_URL`, `E2E_WEB_URL`)
- [ ] Fresh reset, migrate (through the compiled migrate entry), seed; `run-golden-path` on the dev stack
- [ ] `sst` config type-checks; no secret values anywhere in git (`gitleaks`-style scan)
- [ ] Pushed to `main`

## Build log
- 2026-09-29 Cards written (T-24-1..4). Grant T-24-1: `invai-web/vite.config.ts` and `src/lib/build/csp.ts`, prod `connect-src` only (B-190), web-engineer co-reviews. T-24-1 started (runs beside wave 22's T-22-2 and T-22-3; 3 builders).
