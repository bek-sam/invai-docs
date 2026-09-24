# InvAI runbook

Operating the platform: first-time setup, environment variables, how mock providers become real
ones, migrations and seed, the job/queue system, troubleshooting, and deploying to AWS.

## 1. Local setup from a clean Mac

1. **Homebrew** (if not already installed): `/bin/bash -c "$(curl -fsSL
   https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`.
2. **OrbStack** (Docker, lighter than Docker Desktop): `brew install --cask orbstack`, then open
   it once so its CLI (`orb`) is set up. `docker info` should succeed afterwards; if it doesn't,
   run `orb start`.
3. **pnpm**, which also manages its own Node install (Corepack works too, but the workspace
   standardizes on pnpm's own runtime so every machine gets the same Node version):
   ```
   curl -fsSL https://get.pnpm.io/install.sh | sh -
   export PATH="$HOME/.local/share/pnpm/bin:$HOME/.local/share/pnpm:$PATH"   # add to ~/.zshrc
   pnpm env use --global 24
   pnpm --version   # 12.x
   node --version   # v24.x
   ```
   **Every shell that runs `node` or `pnpm` in this workspace must have that `PATH` line first.**
   The system `/usr/local/bin/node` (Node 22, from Homebrew or elsewhere) must not be picked up
   instead — check `which node` resolves under `~/.local/share/pnpm` before running anything.
4. **uv** (Python, for `invai-imaging`): `curl -LsSf https://astral.sh/uv/install.sh | sh`. `uv`
   downloads Python 3.13 itself; no separate Python install is needed.
5. Clone all 8 repos side by side in one parent folder (this one): `invai-contracts`,
   `invai-ui`, `invai-backend`, `invai-imaging`, `invai-web`, `invai-floor`, `invai-infra`,
   `invai-docs`. They are separate git repos, not a monorepo — `invai-backend`, `invai-web` and
   `invai-floor` link `@invai/contracts` (and `@invai/ui` for web/floor) with `link:../<repo>`,
   so the sibling layout is required, not optional.
6. From `invai-infra`: `pnpm install && pnpm dev:all`. See the workspace `README.md` for what
   that does and the demo logins it seeds.

## 2. Environment variables

Each app has its own `.env` (copy from `.env.example`). Defaults already point at the local
Postgres/Redis/MinIO from `invai-infra/local`.

### invai-backend (api + worker)

| Variable | Default (local) | Purpose |
| --- | --- | --- |
| `NODE_ENV` | `development` | `test` points the DB URLs at `invai_test` automatically |
| `PORT` | `3000` | API port |
| `LOG_LEVEL` | `info` | `debug`/`info`/`warn`/`error` |
| `DATABASE_URL` | `postgres://invai_app:invai@localhost:5432/invai` | App connection, RLS enforced |
| `MIGRATION_DATABASE_URL` | `postgres://invai:invai@localhost:5432/invai` | Owner connection: migrations, seed, outbox relay, cross-tenant jobs |
| `TEST_DATABASE_URL` / `TEST_MIGRATION_DATABASE_URL` | unset (derived) | Optional overrides; tests default to the same servers, database `invai_test` |
| `REDIS_URL` | `redis://localhost:6379` | BullMQ, rate limits, floor token cache |
| `S3_BUCKET` | `invai-local` | |
| `S3_REGION` | `us-east-1` | |
| `S3_ENDPOINT` | `http://localhost:9000` | MinIO; unset/different in AWS |
| `S3_ACCESS_KEY_ID` / `S3_SECRET_ACCESS_KEY` | `invai` / `invai-secret` | MinIO credentials locally; IAM role in AWS |
| `S3_FORCE_PATH_STYLE` | `true` | Needed for MinIO; not for real S3 |
| `S3_PUBLIC_ENDPOINT` | unset | Optional, when the browser can't reach `S3_ENDPOINT` directly |
| `IMAGING_URL` | `http://localhost:8000` | |
| `BETTER_AUTH_SECRET` | dev placeholder, 32+ chars | Required; a real random secret in every non-local environment |
| `BETTER_AUTH_URL` | `http://localhost:3000` | |
| `WEB_ORIGIN` | `http://localhost:5173` | CORS |
| `FLOOR_ORIGIN` | `http://localhost:5174` | CORS |
| `FLOOR_TOKEN_SECRET` | unset (falls back to `BETTER_AUTH_SECRET`) | Signs floor session tokens / PIN hashes; set separately in production (S-30) |
| `FLOOR_SESSION_TTL_HOURS` | `12` | |
| `FIELD_ENCRYPTION_KEY` | dev key, format `k1:<base64 32 bytes>` | Encrypts buyer PII and channel tokens. Rotate by prepending a new key: `k2:<base64>,k1:<base64>` — old ciphertext still decrypts |
| `ANTHROPIC_API_KEY` | empty → mock | See §3 |
| `EASYPOST_API_KEY` | empty → mock | See §3 |
| `SHOPIFY_API_KEY` / `SHOPIFY_API_SECRET` | empty → mock | See §3 |
| `SS_ACTIVEWEAR_ACCOUNT` / `SS_ACTIVEWEAR_API_KEY` | empty → mock | See §3 |
| `STRIPE_SECRET_KEY` | empty → mock | See §3 |

`src/env.ts` validates all of this with Zod at startup (`@t3-oss/env-core`) and computes
`env.mocks.{ai,carrier,shopify,supplier,billing}` — `true` whenever the matching key(s) are
missing. `.env`/`.env.local` are loaded automatically outside `production` (Node 24's built-in
`process.loadEnvFile`); production environments must inject real env vars instead.

### invai-web

| Variable | Default | Purpose |
| --- | --- | --- |
| `VITE_API_URL` | `http://localhost:3000` | The API origin the SPA calls |

### invai-floor

| Variable | Default | Purpose |
| --- | --- | --- |
| `VITE_API_URL` | empty (same-origin; `pnpm dev` proxies `/rpc` and `/events` to `http://localhost:3000`) | Set a full URL when the API is on another origin — the backend must then allow that origin in CORS (`FLOOR_ORIGIN`) |
| `VITE_AUTO_LOCK_MINUTES` | `10` | Minutes of inactivity before the station locks back to the PIN screen |

### invai-imaging

| Variable | Default | Purpose |
| --- | --- | --- |
| `STORAGE` | `s3` | `s3` (S3/MinIO) or `local` (files under `LOCAL_STORAGE_DIR`, used by tests) |
| `LOCAL_STORAGE_DIR` | `./.storage` | Only used when `STORAGE=local` |
| `S3_BUCKET` | `invai-local` | |
| `S3_ENDPOINT` | `http://localhost:9000` | |
| `S3_REGION` | `us-east-1` | |
| `S3_ACCESS_KEY_ID` / `S3_SECRET_ACCESS_KEY` | `invai` / `invai-secret` | |
| `S3_CREATE_BUCKET` | `true` | Creates `S3_BUCKET` at startup if missing |
| `TMP_DIR` | system temp | Scratch space for downloads and big renders; a 240" sheet needs about 1 GB |

### invai-infra

No `.env` of its own locally (`local/docker-compose.yml` sets the infra containers' env inline).
AWS stage config and secrets are set with `sst secret set <Name> <value> --stage <stage>` — see
§6.

## 3. Mock providers and how they become real

Every external integration has a mock that runs automatically when its key is missing, so the
whole platform works end to end with no accounts at all. Add the key and restart the API/worker
to switch that one integration to the real thing — nothing else changes.

| Integration | Env var(s) that switch it on | Mock behavior | Real adapter |
| --- | --- | --- | --- |
| AI (Claude) | `ANTHROPIC_API_KEY` | Deterministic, schema-valid output (listings, trademark judging, assistant) | `invai-backend/src/ai/providers/anthropic.ts` |
| Shipping (EasyPost) | `EASYPOST_API_KEY` | In-process mock carrier: fake rates, a mock tracking code, a real 4x6 PDF via imaging's `/labels/mock` | `invai-backend/src/integrations/carriers/easypost` |
| Shopify | `SHOPIFY_API_KEY` **and** `SHOPIFY_API_SECRET` (both required) | In-memory mock store that "receives" 1–3 new orders per poll | `invai-backend/src/integrations/channels/shopify/live.ts` (OAuth + webhooks); `.../mock.ts` is the mock |
| S&S Activewear | `SS_ACTIVEWEAR_ACCOUNT` **and** `SS_ACTIVEWEAR_API_KEY` (both required) | Static catalog + stock mock | `invai-backend/src/integrations/suppliers` |
| Stripe (billing) | `STRIPE_SECRET_KEY` | Plan limits still enforced from the plan catalog; checkout is stubbed | Not implemented for v1 — plan limits matter more than payment tonight |

Etsy, Amazon, TikTok and Walmart have no live adapter yet (CSV import only); their marketplace
approvals, not code, are the blocker. In production, `app.ts` also returns `404` for
`/webhooks/shopify*` while Shopify is mocked, since the mock's webhook secret is a public
constant — see security review S-14.

## 4. Migrations and seed

```
cd invai-backend
pnpm db:generate   # drizzle-kit generate — writes a new migration from schema changes
pnpm db:migrate     # tsx src/db/migrate.ts — applies pending migrations, owner connection
pnpm db:seed        # tsx src/db/seed/index.ts — creates the "Desert Bloom Tees" demo shop
pnpm db:reset       # tsx src/db/reset.ts — drops and recreates the schema, then re-migrate
pnpm db:studio      # drizzle-kit studio — browse the database
```

- `db:seed` is safe to run more than once: it checks for a company with slug `desert-bloom-tees`
  first and exits with a warning (not an error) if it's already there. To start over: `pnpm
  db:reset && pnpm db:migrate && pnpm db:seed`.
- Seeding takes roughly 15–20 minutes (about 300 orders, 670 order items, real gang-sheet files
  composed through imaging, sample art generated per design) and writes
  `invai-backend/seed-output.json` with the generated ids, demo logins, PINs and a station token
  for "Press 1" — the same information is in the workspace `README.md`.
- Migrations run as the `invai` owner role (`MIGRATION_DATABASE_URL`); the API and worker always
  run as `invai_app`, which is not the table owner and has no `BYPASSRLS` — row-level security is
  enforced even for a bug in application code, not just for the browser's requests.

## 5. Queues and the outbox relay

Every state change writes its row and an `outbox_events` row in the same Postgres transaction
(`invai-backend/src/lib/outbox.ts`). A relay (`src/worker/outbox-relay.ts`, started inside
`pnpm dev:worker` / `src/worker/index.ts`) polls undispatched outbox rows and pushes them into
BullMQ. This means an event is never lost when a process crashes mid-request, and no event fires
for a change that then rolled back.

Five BullMQ queues (`src/lib/queues.ts`), one `Worker` per queue in the same process:

| Queue | Examples |
| --- | --- |
| `sync` | Fetch orders, webhook processing, listing/availability sync |
| `render` | Personalization rendering, gang-sheet compose (CPU/memory heavy) |
| `ship` | Buy labels, push tracking |
| `ai` | Listing drafts, trademark checks, assistant tool calls, batches |
| `reports` | Profit recompute, nightly PII purge/sweep |

Jobs are idempotent (a stable `jobId`, e.g. `push-tracking:{shipmentId}`), so a retry after a
crash can't double-ship a label or double-push tracking. Failed jobs retry with backoff.

## 6. Troubleshooting

| Symptom | Fix |
| --- | --- |
| `docker info` hangs or errors, `docker compose up` never starts | OrbStack occasionally hangs. `orb stop && orb start`, then retry. |
| `pnpm dev:api` / `pnpm dev:worker` keep restarting on their own | `tsx watch` restarts on *any* file save under `src/`, including edits from another process working in the same repo at the same time. This is expected during active development; before an end-to-end or demo run, stop and restart every process once so nothing is running against stale code, and check for a second, non-watch process left over from an earlier run still holding the same queues (`ps aux \| grep tsx`, or check who's listening on :3000). |
| MinIO container fails to pull / `minio/minio` not found | The Docker Hub image `minio/minio` no longer exists. `local/docker-compose.yml` pulls `quay.io/minio/minio` instead — make sure you're on the current compose file, not a cached older one. |
| A fresh `docker compose build` (the `full` profile) fails pulling packages that were "just published" | pnpm's `minimumReleaseAge` policy refuses very recently published package versions inside a from-scratch Docker build. It clears on its own after the package has aged; a pinned `minimumReleaseAgeExclude` for the packages you control is the other option (open issue in `v1-plan.md` #2). |
| `node --version` shows v22 instead of v24, or `pnpm` isn't found | The `PATH` line from §1 wasn't run in this shell, or something in `~/.zshrc`/`~/.zprofile` puts `/usr/local/bin` ahead of `~/.local/share/pnpm/bin`. Run `which node` and confirm it resolves under `~/.local/share/pnpm` before doing anything else. |
| Port 5432/6379/9000/3000/8000/5173/5174 already in use | Check nothing else on the machine owns it — in particular, **port 54322 belongs to another project's Supabase on this machine and must be left alone**; InvAI never uses it. |
| Floor tablet won't connect after pairing | Station tokens are shown once. Re-pair from **Settings → Stations → Pair tablet** to issue a new one; the old one stops working immediately. |
| `pnpm db:seed` says the company already exists | Expected on a second run — not a failure. Use `pnpm db:reset && pnpm db:migrate && pnpm db:seed` to start over. |

## 7. Deploying to AWS (SST)

`invai-infra/sst.config.ts` (SST 4.17.1) defines, per stage (`staging`, `production`):

**Configured and working (as far as it can be verified without AWS credentials — `pnpm
typecheck` passes; deploy itself is unverified here):**

- VPC with a NAT EC2 instance instead of NAT Gateways.
- RDS Postgres 17, encrypted at rest, private subnets, RDS Proxy on for `production`.
- Valkey via `sst.aws.Redis` (`engine: "valkey"`).
- A private S3 bucket with lifecycle rules (`sheets/` expires after 90 days, `raw/` after 30,
  matching `architecture.md` §7).
- A customer-managed KMS key for field-level encryption.
- An ECS cluster: `api` (public, load-balanced, health-checked on `/health`), `worker` and
  `imaging` (internal only, reached over service discovery).
- Static sites for `web` and `floor` (`sst.aws.StaticSite`, built with `pnpm build`).
- Secrets via `sst.Secret`: `BetterAuthSecret` and `FieldEncryptionKey` are required (deploy
  fails if unset, no placeholder); `AnthropicApiKey`, `EasyPostApiKey`, `ShopifyApiKey`,
  `ShopifyApiSecret` default to `""` (mock providers in AWS too, until a key is set with `sst
  secret set`).
- `production` has `removal: "retain"` and `protect: true`.

**Still placeholder / needs a human with real AWS and GitHub access:**

- Nothing provisions the low-privilege `invai_app` role in RDS the way `local/init.sql` does
  locally — needs a one-time bootstrap script or an SST dynamic provider before the app can
  connect with RLS enforced the same way it does locally.
- `.github/workflows/deploy.yml`'s `role-to-assume` is a placeholder ARN
  (`arn:aws:iam::123456789012:role/invai-deploy`) and the deploy secrets aren't set — the
  workflow can't actually run yet.
- The SES email identity defaults to `<stage>.invai.example`; swap in a real sending domain and
  verify it before any email goes out.

```
cd invai-infra
pnpm install
pnpm typecheck
pnpm deploy:staging   # sst deploy --stage staging
pnpm deploy:prod      # sst deploy --stage production
```

CI (`.github/workflows/deploy.yml`) runs the same deploy via OIDC role assumption, triggered
manually (`workflow_dispatch`, choose the stage) or by a `v*` tag push (always `production`).
