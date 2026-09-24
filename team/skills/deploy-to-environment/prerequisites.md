# Deploy prerequisites (checked against the repos on 2026-09-24)

Sources: `research/11-platform-scale-playbook.md` §10 (gaps G1–G20) and §0, `research/12-security-quality-playbook.md` §7, `build/runbook.md` §7, `invai-infra/sst.config.ts`, `invai-infra/.github/workflows/deploy.yml`, `waves/backlog.md`.

Mark each row `done (evidence)`, `open`, or `accepted by owner (OI-n)` in the release record. **Blocks** says which stage it blocks. "Staging" means synthetic seed data only; "production" means any real shop data.

## A. Infrastructure (research 11)
| # | Prerequisite | Today | Evidence to check | Blocks | Backlog |
|---|---|---|---|---|---|
| G1 | App connects as `invai_app` (no BYPASSRLS), not the RDS master user; `invai_system` role for relay and cross-tenant jobs | **Open**: `sharedEnvironment.DATABASE_URL = MIGRATION_DATABASE_URL = databaseUrl` (master) in `sst.config.ts`, so RLS is off in AWS | `grep -n "DATABASE_URL" invai-infra/sst.config.ts` | staging and production | B-01 |
| G2 | Valkey `cluster: false` and `maxmemory-policy noeviction` (BullMQ needs both) | **Open**: `new sst.aws.Redis("Redis", { vpc, engine: "valkey" })` sets neither; SST defaults to cluster mode | `grep -n "sst.aws.Redis" invai-infra/sst.config.ts` | staging and production | B-02 |
| G3 | Migrations run as a separate step before the service update | **Open**: `deploy.yml` has no migrate step; the backend build doesn't emit a migrate entry point | `grep -n migrat invai-infra/.github/workflows/deploy.yml` | any release with a new migration | B-03 |
| G4 | HTTPS: 443 listener with an ACM certificate, 80 redirects to 443 | **Open**: `listen: "80/http"` only | `grep -n listen invai-infra/sst.config.ts` | production (and staging with real logins) | B-03 |
| G5 | RDS instance size set (not `t4g.micro`), backup retention 14 d staging / 35 d production, deletion protection; decide on RDS Proxy (pins every connection with `set_config`) | **Open**: `sst.aws.Postgres("Db", { vpc, version: "17", proxy: isProd })` | `grep -n "sst.aws.Postgres" -A4 invai-infra/sst.config.ts` | production | B-37 (sizing), none for retention yet |
| G6 | Role-level `statement_timeout`, `idle_in_transaction_session_timeout`, `lock_timeout` | **Open** | `select rolname, rolconfig from pg_roles where rolname like 'invai%';` | production | B-16 |
| G7 | ALB health check on `/livez` (process only); `/readyz` for DB and Valkey | **Open**: ALB uses `/health`, which checks DB and Redis | `grep -n health invai-infra/sst.config.ts` | production | B-16 |
| G8 | Graceful SIGTERM drain in the API; worker `stopTimeout` ≥ 60 s | **Open** | `grep -n SIGTERM invai-backend/src/api/server.ts` | production | B-16 |
| G9–G11 | Retry jitter, `UnrecoverableError`, DLQ alert; outbox purge and parked-event alert | **Open** | `invai-backend/src/lib/queues.ts`, `src/worker/outbox-relay.ts` | production | B-17 |
| G14 | Logs with `company_id`, `request_id`, `trace_id`; redaction; alerts wired | **Open** | `add-observability` | production | B-18 |
| G15 | Imaging concurrency limit (8 GB task, ~1 GB per 240" sheet) | **Open** | `invai-imaging/app/main.py` | production | B-19 |
| — | ECS circuit breaker with alarm rollback | **Open** | `sst.config.ts` services have no `transform` for it | production | none yet |

## B. Deploy pipeline and config (runbook §7)
| Prerequisite | Today | Blocks |
|---|---|---|
| `deploy.yml` `role-to-assume` is a real OIDC role (trust restricted to `bek-sam/invai-infra` tags and environments) | **Open**: placeholder `arn:aws:iam::123456789012:role/invai-deploy` | CI deploys (a local `pnpm deploy:<stage>` by the owner doesn't need it) |
| Deploy-key secrets set in `invai-infra`: `BACKEND_DEPLOY_KEY`, `IMAGING_DEPLOY_KEY`, `WEB_DEPLOY_KEY`, `FLOOR_DEPLOY_KEY`, `CONTRACTS_DEPLOY_KEY`, `UI_DEPLOY_KEY` | **Open** (owner sets secrets) | CI deploys |
| `deploy.yml` requires green CI at the deployed SHAs (research 12 G19) | **Open** | production |
| `sst secret set BetterAuthSecret …` and `FieldEncryptionKey …` for the stage (required; deploy fails without them) | owner, per stage | every stage |
| Optional integration secrets (`AnthropicApiKey`, `EasyPostApiKey`, `ShopifyApiKey`, `ShopifyApiSecret`) stay empty → mocks, unless the owner decides otherwise | owner | — |
| `FLOOR_TOKEN_SECRET` set separately from `BETTER_AUTH_SECRET` (S-30, research 12 G9); not wired in `sst.config.ts` today | **Open** | production |
| Real domains: `BETTER_AUTH_URL` and `WEB_ORIGIN` are `*.invai.example` in `sst.config.ts`; `FLOOR_ORIGIN` isn't set | **Open** | production (and staging logins from a browser) |
| SES identity for a real sending domain, verified, out of the SES sandbox | **Open**: defaults to `<stage>.invai.example` | any environment that sends email |

## C. Before real shop data (research 12 §7, operating system)
Real shop data in any non-local environment is itself an owner decision. On top of A and B:
- Dependency, secret and container scanning in CI (G18, B-08), actions and images pinned, non-root containers (G15–G17, B-21).
- Email verification and MFA for owners and admins (G1, B-09).
- Written incident-response plan, access-control policy, vendor inventory, DPA and sub-processor list (G29, B-10).
- KMS envelope encryption instead of the static `FIELD_ENCRYPTION_KEY` (G11, B-23) before the Amazon SP-API application.
- Central log retention ≥ 12 months and alerting (G30).
- A tested restore (`backup-restore-drill`) with RTO recorded.
