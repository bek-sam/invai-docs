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
   that does and the demo logins it seeds. Stop the app processes with **Ctrl-C** in that
   terminal; `cd invai-infra && pnpm stop` separately stops the Docker infra (Postgres, Valkey,
   MinIO, Mailpit) and keeps its data volumes — see §7 for both.

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
| `IMAGING_SHARED_SECRET` | dev default (`invai-imaging-dev-secret`) outside production, unset in production | Sent as `X-Imaging-Secret`; imaging requires 32+ chars and refuses the dev secret in production |
| `BETTER_AUTH_SECRET` | dev placeholder, 32+ chars | Required; a real random secret in every non-local environment. **No rotation support** (unlike `FIELD_ENCRYPTION_KEY`): it's one value, not a `k1:,k2:` list. Changing it signs out every session and makes every already-enrolled TOTP secret (two-step sign-in) undecryptable — those users must turn two-step sign-in off and back on to re-enroll |
| `BETTER_AUTH_URL` | `http://localhost:3000` | |
| `WEB_ORIGIN` | `http://localhost:5173` | CORS |
| `FLOOR_ORIGIN` | `http://localhost:5174` | CORS |
| `FLOOR_TOKEN_SECRET` | unset (falls back to `BETTER_AUTH_SECRET`) | Signs floor session tokens / PIN hashes; set separately in production (S-30) |
| `FLOOR_SESSION_TTL_HOURS` | `12` | |
| `MIN_FLOOR_CONTRACT_VERSION` | contracts' `FLOOR_COMPAT_BASELINE` | Oldest `X-Contract-Version` a floor tablet may call with (ADR 0012). Emergency/rollback override only — bumping the contract version alone never refuses current tablets |
| `FIELD_ENCRYPTION_KEY` | dev key, format `k1:<base64 32 bytes>` | Encrypts buyer PII and channel tokens. Rotate by prepending a new key: `k2:<base64>,k1:<base64>` — old ciphertext still decrypts |
| `ANTHROPIC_API_KEY` | empty → mock | See §3. Wins over `OPENAI_API_KEY` when both are set (ADR 0021) |
| `OPENAI_API_KEY` | empty | Used only when `ANTHROPIC_API_KEY` is empty (ADR 0021): every AI route then runs on OpenAI. Neither key → mock. Both are ignored under `NODE_ENV=test` |
| `INTERNAL_ADMIN_TOKEN` | unset → operator DLQ routes 404 | `X-Internal-Token` for the internal dead-letter/redrive routes (`src/api/internal.ts`); never shipped to a browser |
| `AI_DAILY_PLATFORM_CAP_CENTS` / `AI_DAILY_TENANT_CAP_CENTS` | `50000` / `5000` | Daily (UTC) real-model AI spend caps; `0` turns that cap off |
| `EASYPOST_API_KEY` | empty → mock | See §3 |
| `EASYPOST_WEBHOOK_SECRET` | unset → mock dev secret | EasyPost webhook HMAC (`X-Hmac-Signature`) |
| `SHOPIFY_API_KEY` / `SHOPIFY_API_SECRET` | empty → mock | See §3 |
| `SS_ACTIVEWEAR_ACCOUNT` / `SS_ACTIVEWEAR_API_KEY` | empty → mock | See §3 |
| `STRIPE_SECRET_KEY` | empty → mock | See §3 |
| `STRIPE_WEBHOOK_SECRET` | unset | Stripe webhook signature check; required in production (see `PRODUCTION_KEYS` below) |
| `CENSUS_API_KEY` / `GOOGLE_TRENDS_API_KEY` / `PINTEREST_API_KEY` / `JUNGLE_SCOUT_API_KEY` | empty → mock | Market-signal demand providers (wave 18). Free/unpriced today; none is required in production, so InvAI runs the mock market providers there until a key is set |
| `MARKET_MOCK_FAIL` | unset | Test-only: comma list of `SignalSource`s (e.g. `google_trends,pinterest_trends`) whose mock throws instead of returning data. Always empty in production, whatever this is set to |
| `SMTP_URL` | `smtp://localhost:1025` (Mailpit) outside production; unset in production unless `ALLOW_MOCKS=true` | Outgoing mail. A missing value outside production means Mailpit; in production a missing value means the mailer logs instead of sending |
| `MAIL_FROM` | `InvAI <sheets@invai.local>` outside production | From address on every outgoing email |
| `MAIL_POSTAL_ADDRESS` | placeholder pending OI-12 | Printed in the footer of every person-facing email (CAN-SPAM) |
| `DIGEST_ENABLED` | `true` | `false` stops every weekly-digest build |
| `DIGEST_EMAIL_ENABLED` | `false` in production, `true` elsewhere | Keeps digests in-app only when `false` (`sendUserEmail` answers `skipped: disabled`); production stays off even with `SMTP_URL` set, until OI-12/13/14 are answered. Setting it explicitly always wins |
| `DIGEST_SUMMARY_MODE` | `shadow` | `off` / `shadow` (built, stored, never shown or sent) / `on`. Stays `shadow` until OI-8 |
| `DIGEST_MAX_CENTS_PER_WEEK` | `10` | Per-shop cap on the digest's AI summary spend, in cents/week |
| `ALLOW_MOCKS` | `false` | Lets production boot on mock providers anyway (demo/staging stages only), with a startup warning. Without it, production refuses to start while any `PRODUCTION_KEYS` entry is missing |

`src/env.ts` validates all of this with Zod at startup (`@t3-oss/env-core`) and computes
`env.mocks.{ai,carrier,shopify,supplier,billing,mail,census,googleTrends,pinterest,jungleScout}` —
`true` whenever the matching key(s) are missing. `.env`/`.env.local` are loaded automatically
outside `production` (Node 24's built-in `process.loadEnvFile`); production environments must
inject real env vars instead.

Production refuses to start if any of `PRODUCTION_KEYS` (`src/env.ts`) is missing —
`EASYPOST_API_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY`),
`SHOPIFY_API_KEY`, `SHOPIFY_API_SECRET`, `SMTP_URL`, `MAIL_FROM`, `IMAGING_SHARED_SECRET` — unless
`ALLOW_MOCKS=true`. Supplier (S&S) keys aren't in that list: those are tenant-owned, not
platform-wide.

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
§8.

## 3. Mock providers and how they become real

Every external integration has a mock that runs automatically when its key is missing, so the
whole platform works end to end with no accounts at all. Add the key and restart the API/worker
to switch that one integration to the real thing — nothing else changes.

| Integration | Env var(s) that switch it on | Mock behavior | Real adapter |
| --- | --- | --- | --- |
| AI (Claude, or OpenAI without a Claude key) | `ANTHROPIC_API_KEY`, else `OPENAI_API_KEY` (ADR 0021) | Deterministic, schema-valid output (listings, trademark judging, assistant) | `invai-backend/src/ai/providers/anthropic.ts`, `.../openai.ts`. Check which one runs: `pnpm evals assistant` prints `mode: anthropic`, `openai` or `mock` |
| Shipping (EasyPost) | `EASYPOST_API_KEY` | In-process mock carrier: fake rates, a mock tracking code, a real 4x6 PDF via imaging's `/labels/mock` | `invai-backend/src/integrations/carriers/easypost` |
| Shopify | `SHOPIFY_API_KEY` **and** `SHOPIFY_API_SECRET` (both required) | In-memory mock store that "receives" 1–3 new orders per poll | `invai-backend/src/integrations/channels/shopify/live.ts` (OAuth + webhooks); `.../mock.ts` is the mock |
| S&S Activewear | `SS_ACTIVEWEAR_ACCOUNT` **and** `SS_ACTIVEWEAR_API_KEY` (both required) | Static catalog + stock mock | `invai-backend/src/integrations/suppliers` |
| Stripe (billing) | `STRIPE_SECRET_KEY` | Plan limits still enforced from the plan catalog; checkout is stubbed | Not implemented for v1 — plan limits matter more than payment tonight |
| Mail (weekly digest, invites, account emails) | `SMTP_URL` | Mailpit (`local/docker-compose.yml`, SMTP :1025, UI http://localhost:8025) | Any SMTP server via `SMTP_URL`; production stays off unless `SMTP_URL` and `MAIL_FROM` are both set (`PRODUCTION_KEYS`) |

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
pnpm db:reset       # tsx src/db/reset.ts — drops and recreates the public/drizzle schemas
pnpm db:studio      # drizzle-kit studio — browse the database
```

- To start over: `pnpm db:reset && pnpm db:migrate && pnpm db:seed`, imaging up and **no worker
  needed to be stopped first** (see "Seeding next to a running worker" below) — start the worker
  before or after the seed, either order is fine.
- `db:reset` drops and recreates the schema (it does not run migrations itself — `db:migrate` is
  the next step, always), **and** it empties the app's five BullMQ queues (`sync`, `render`,
  `ship`, `ai`, `reports`) in the Redis DB of `REDIS_URL` — only `bull:<queue>:*` keys; rate-limit
  (`rl:`), realtime (`rt:`) and every other Redis DB are untouched. It prints the jobs removed per
  queue, e.g. `[reset] queues obliterated in /0: {"sync":8,"render":42,...}`. **Restart a worker
  that was already running** after a reset — its repeatable sweeps only re-register on start; a
  worker that was already running when you reset keeps running but won't re-arm those sweeps on
  its own. Refuses to run under `NODE_ENV=production`.
  - Fixes wave 19 gate issue 6 (a worker started after a reset used to replay stale jobs for rows
    that no longer existed — that was Redis holding leftover jobs across the schema wipe, not a
    bug in the jobs themselves).
- `db:seed` is safe to run more than once: it checks for a company with slug `desert-bloom-tees`
  first and exits with a warning (not an error) if it's already there.
- Seeding takes about 25 seconds to a couple of minutes (25–100 s measured, imaging cached vs.
  cold; not the 15–20 minutes an earlier version of this doc said) for roughly 300–360 orders,
  680–700 order items, real gang-sheet files composed through imaging, sample art generated per
  design, and writes
  `invai-backend/seed-output.json` with the generated ids, demo logins, PINs and a station token
  for "Press 1" — the same information is in the workspace `README.md`. Imaging must be running so
  the seed can render real sample art; a missing imaging service makes the seed fail, not fall
  back to placeholders.
- **Seeding next to a running worker:** the seed builder parks each phase's outbox events inside
  the same transaction that emits them and releases them all once at the end, so a worker running
  during the seed never dispatches jobs for a half-built company — it sees the finished shop
  exactly as if it had started after the seed. Right after `[seed] done`, expect the worker to add
  a burst of `profit.recomputed`, `design.qa_completed` and `credits.consumed` events as it catches
  up; that's expected, not a sign something is wrong.
- **Seeding a database copy** (for an isolated test run without touching the shared dev DB): set
  `DATABASE_URL`, `MIGRATION_DATABASE_URL` and `REDIS_URL` (your own Redis DB, e.g.
  `redis://localhost:6379/14`) to the copy, and `SEED_OUTPUT_FILE=<path>` so the run writes there
  instead of overwriting the shared `invai-backend/seed-output.json`. A copy made with `docker exec
  local-postgres-1 createdb -U invai -T invai <copy>` doesn't carry the `invai_app` grants that
  later migrations add — reapply them from `drizzle/0001_grants_extensions.sql` on the copy before
  migrating it (wave 20 lesson).
- `pnpm test` (in `invai-backend`) uses `REDIS_URL` as-is — it is **not** rewritten to a test DB
  the way the Postgres URLs are under `NODE_ENV=test`. Pin `REDIS_URL=redis://localhost:6379/<n>`
  to an unused DB (1–15) for a test run if a dev worker is running on DB 0, or its queues get
  obliterated by `reset.test.ts`-style test runs the same way `db:reset` does.
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
`pnpm db:reset` empties all five queues in `REDIS_URL` — see §4.

## 6. End-to-end tests

| Suite | Command | Notes |
| --- | --- | --- |
| Backend unit/integration | `cd invai-backend && pnpm test` | Runs against `invai_test` through `src/test/fixtures.ts`; never touches the shared dev DB |
| Web browser E2E | `cd invai-web && pnpm e2e` | Playwright (`playwright.config.ts`); needs `pnpm dev:all` already running |
| Web API golden path | `cd invai-web && E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts` | Run on a **fresh seed** (`db:reset && db:migrate && db:seed`) — it asserts on seed counts |
| Floor browser E2E | `cd invai-floor && pnpm e2e` | Playwright (`playwright.config.ts`) |

Run `db:reset → db:migrate → db:seed`, in that order, before reading the worker log or running the
golden path — the worker's relay logs `relation ... does not exist` until `db:migrate` finishes,
which is expected mid-sequence, not a failure. Don't `pnpm db:reset` the shared dev DB while other
agents or processes are using it; use your own database copy (§4) for a one-off E2E run instead.

## 7. Troubleshooting

| Symptom | Fix |
| --- | --- |
| `docker info` hangs, `docker ps` hangs, or `docker compose up` never starts | Check `docker ps` first — if *that* hangs, every Postgres/Redis/MinIO call from every process blocks with no error, which looks like a stalled agent or a usage-limit stop, not an infra problem. `orb stop && orb start`, then `cd invai-infra/local && docker compose up -d` (volumes survive). |
| `pnpm dev:api` / `pnpm dev:worker` keep restarting on their own | `tsx watch` restarts on *any* file save under `src/`, including edits from another process working in the same repo at the same time. This is expected during active development; before an end-to-end or demo run, stop and restart every process once so nothing is running against stale code, and check for a second, non-watch process left over from an earlier run still holding the same queues (`ps aux \| grep tsx`, or check who's listening on :3000). |
| A request dies mid-response | Likely `tsx watch` restarting the API from someone else's edit (previous row). Retry the request once; if it dies again, it's a real failure. |
| MinIO container fails to pull / `minio/minio` not found | The Docker Hub image `minio/minio` no longer exists. `local/docker-compose.yml` pulls `quay.io/minio/minio` instead — make sure you're on the current compose file, not a cached older one. |
| A fresh `docker compose build` (the `full` profile) fails pulling packages that were "just published" | pnpm's `minimumReleaseAge` policy refuses very recently published package versions inside a from-scratch Docker build. It clears on its own after the package has aged; a pinned `minimumReleaseAgeExclude` for the packages you control is the other option (open issue in `v1-plan.md` #2). |
| `node --version` shows v22 instead of v24, or `pnpm` isn't found | The `PATH` line from §1 wasn't run in this shell, or something in `~/.zshrc`/`~/.zprofile` puts `/usr/local/bin` ahead of `~/.local/share/pnpm/bin`. Run `which node` and confirm it resolves under `~/.local/share/pnpm` before doing anything else. |
| Port 5432/6379/9000/3000/8000/5173/5174 already in use | Check nothing else on the machine owns it — in particular, **port 54322 belongs to another project's Supabase on this machine and must be left alone**; InvAI never uses it. |
| Floor tablet won't connect after pairing | Station tokens are shown once. Re-pair from **Settings → Stations → Pair tablet** to issue a new one; the old one stops working immediately. |
| `pnpm db:seed` says the company already exists | Expected on a second run — not a failure. Use `pnpm db:reset && pnpm db:migrate && pnpm db:seed` to start over. |
| A database copy (`createdb -T invai`) fails with permission errors once you migrate or seed it | Template copies don't carry the `invai_app` grants that later migrations add. Reapply `drizzle/0001_grants_extensions.sql` on the copy first. |
| A worker started right after `pnpm db:reset` seems to replay jobs for rows that no longer exist | Fixed: `db:reset` now empties the five app queues in `REDIS_URL` itself (§4). If you still see it, you're on an older build, or you reset a *different* Redis DB than the worker's `REDIS_URL` points at — check both match. |
| `pnpm stop` didn't stop the api/worker/imaging/web/floor processes | `pnpm stop` (`invai-infra/scripts/stop.sh`) only stops the **Docker infra** (Postgres, Valkey, MinIO, Mailpit) — data volumes are kept. The app processes started by `pnpm dev:all` run in the foreground under `concurrently`; stop those with **Ctrl-C** in that terminal. |

## 8. Deploying to AWS (SST)

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
