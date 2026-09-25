# Wave 3 integration gate

- Run by: qa-engineer, 2026-09-25
- Result: **green. Recommendation: push.**
- Evidence: logs in `/tmp/gate3/*.log` (temporary, this machine only). Screenshots in
  `invai-docs/waves/3/gate/`.

## What was tested (local `main`, not pushed)
| Repo | HEAD | Unpushed commits |
|---|---|---|
| invai-backend | `f036fbd` | 13 (T-3-1 Shopify adapter: `563287b` `cc35a08` `f9140dd` `5a89ba8` `0bb1460` `50e045f` `2a15725` `00c35e4`; T-3-2 EasyPost: `55725bf` `b648cfd`; T-3-3 listings/availability: `b8ac9d0`; T-3-4 heavy work to jobs: `97651a0` `f036fbd`) |
| invai-web | `6718293` | 2 (T-3-4 ship-queue batch-buy poll: `a6ea3a1` `6718293`) |
| invai-contracts | `06e62a3` | 1 (T-3-4 async-result contract stubs) |
| invai-infra, invai-floor, invai-imaging, invai-ui | up to date with origin (infra `148df7d` carries wave 2's `MOCK_CARRIER_TRANSIT_HOURS` default, already reviewed) | 0 |

All 7 product repo working trees were clean before and after the run (`git status --short` empty
in all 7). `invai-docs` has other agents' in-flight uncommitted work (`team/lessons.md`,
`waves/3/wave.md`, `waves/backlog.md`, `waves/3/reports/T-3-3-report.md`, `waves/4/`) — not
touched by this gate; only `waves/3/gate.md` and `waves/3/gate/` are committed here.

All four wave 3 cards (T-3-1 Shopify adapter, T-3-2 EasyPost tracking, T-3-3 listings/
availability push, T-3-4 heavy work to jobs) have every required reviewer's latest file at
`invai-docs/waves/3/reviews/*.md` reading **approve** (T-3-4 went to a round 2 on both `reviewer`
and `web-engineer`, both approved on r2).

## Clean start
- Infra: `local-postgres-1`, `local-valkey-1`, `local-minio-1`, `local-mailpit-1` healthy
  throughout (checked at the start and again at the end, ~13 h uptime, untouched by this gate).
- Ports 3000–3199, 5173, 5174 and 8000 were free before starting; no stale api/worker processes
  (`lsof`/`ps` both empty).
- Node v24.21.0, pnpm 12.6.0.
- `MOCK_CARRIER_TRANSIT_HOURS=0.001` set on every worker start, per `dev.sh`'s default (T-2-6).
- One process-hygiene note: after killing the `dev:all`-spawned worker child once (to seed with
  the worker stopped), its `tsx watch` **parent** process stayed alive with no child — a leftover
  watcher, not a duplicate worker. It was found (`ps aux | grep -i tsx`, comparing the "cli.mjs
  watch" parent lines against the "--require preflight.cjs" child lines) and killed before any
  browser suite ran, so at no point were two live workers processing jobs against the same DB.

## 1. Repo checks
| Repo | typecheck | lint | test | build |
|---|---|---|---|---|
| invai-contracts | pass | pass (46 files) | **31/31** | n/a |
| invai-ui | pass | pass (53 files) | **20/20** | n/a |
| invai-imaging | ruff: pass ("All checks passed!") | n/a | pytest **27/27** | n/a |
| invai-backend | pass | pass (242 files) | **435/435** (54.8 s) | pass (tsup) |
| invai-web | pass | pass (119 files) | **55/55** | pass (vite; chunk-size warning only, pre-existing) |
| invai-floor | pass | pass (57 files) | **41/41** | pass (vite + PWA; chunk-size warning only, pre-existing) |

Backend tests grew from 318 at the wave 2 gate to 435 (T-3-1 Shopify adapter, T-3-2 EasyPost,
T-3-3 listings/availability, T-3-4 jobs). Web tests grew from 47 to 55 (T-3-4's ship-queue poll).

## 2. Database: reset, migrate, reference data, seed
- `db:reset` then `db:migrate` applied all migrations: `drizzle.__drizzle_migrations` has **15**
  rows (0000–0014, matching wave 3's "migrations now run to 0014" — new since wave 2: `0013_carriers_webhook_events`,
  `0014_privacy_requests`).
- `db:seed` ran three times during the gate (initial, before the browser suite, and the final
  cleanup reseed), each time with imaging up and the worker **stopped**, per the wave 3 seed
  rule. All three were clean, EXIT 0, ~22–23 s each:
  `{"orders":360,"items":~672-673,"transitions":~3868-3873,"dueSoon":88}`, 25 sheets, ~581–584
  transfers, 264 shipments, ~108 inventory variants.
- **T-3-3 check — listings exist:** `select count(*) from listings` = **147–148** every run (the
  small run-to-run variance is expected: the seed's listing generation has some randomness, as
  with sheet/transfer counts). Confirmed non-zero on the first seed, and again on the final
  reseed (148).
- Final state left in the shared dev DB: 360 orders, 15 migrations, 148 listings.
  `seed-output.json` was overwritten by the final seed (expected, per instructions and per
  wave.md's T-3-3 follow-up note).

## 3. E2E suites
Health before each run: API `{"ok":true,"db":true,"redis":true,"imaging":true,"s3":true}`,
imaging `{"ok":true,"vips_version":"8.18.6"}`, web and floor both 200.

| Suite | Seed | Result |
|---|---|---|
| `E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts` (invai-web) | fresh seed 1 | **13/13 passed** (13.9 s) |
| Reseed, 65 s pause, `pnpm e2e` (invai-web) | fresh seed 2 | **15/15 passed** (49.5 s) — 13 golden-path steps + `screens.smoke.spec.ts` (owner, 27+ routes, and the vendor portal), console log: "No screen issues." |
| `pnpm e2e` (invai-floor), same stack | seed 2 | **1/1 passed** (3.2 s): station setup, PIN login, press scan check, QC pass, pack |

No retries, sleeps or `.skip` were needed on any suite this gate — everything passed clean on the
first attempt, unlike wave 2's flaky `clickIfShown` episode (fixed then, still fixed now).

## 4. Wave 3 smoke checks (done for real, screenshots in `gate/` where there's UI)

| Check | Result |
|---|---|
| **Batch labels** — select 3 orders on Shipping, "Buy & print all" | **Pass.** Selected 3 ready-to-ship orders (Etsy #3104008806, Amazon #113-2242326-1003458, Etsy #3104010656), clicked "Buy & print 3" (the button's label reflects the selection count). Toast "3 labels bought / Postage $36.18" appeared alongside a "Print 3 labels" button, and the ready-to-ship count dropped from 15 to 12 orders packed (`gate/1-batch-labels-bought.png`). |
| **Large CSV** — generated 400-row CSV import returns `queued` and completes | **Pass.** Generated a 400-row Etsy-format CSV (400 distinct synthetic order ids, above the contract's `CSV_INLINE_MAX_ROWS = 300` threshold), uploaded it and called `channels.importCsv` via the same oRPC client the E2E suites use. First response: `status:"queued"`, `jobId` set, `rowsTotal:400`, zero counts (matches the additive contract stub design exactly). Polled `channels.imports`: `queued` → `running` (counts climbing) → **`completed`**, `ordersImported:400`, `rowsFailed:0`, all within a few seconds. Driven entirely through the API (no UI step specified for this check). |
| **Shopify webhooks (mock-signed)** — unsigned 401; pending payment skipped; `customers/redact` works | **Pass, all three.** (1) Unsigned `POST /webhooks/shopify` → `401 {"error":"invalid signature"}`. (2) A mock-HMAC-signed `orders/create` webhook with `financial_status:"pending"` → `200 {"ok":true}` (queued and answered fast, as designed), and the worker log confirms it was **not** imported: `[channels.sync] webhook skipped {"channel":"shopify","topic":"orders/create","reason":"order 990042 not paid (pending); skipped"}`; order count for the company stayed at 369 both before and after, and no order row exists for that channel order id. (3) A mock-HMAC-signed `customers/redact` webhook for a real seeded Shopify order (`shopify-1202`, which had `buyer_ref` and a `buyer_pii` row before) → `200 {"ok":true,"handled":true}` (compliance topics are handled inline, before the 200, per the code's own comment); confirmed after: `buyer_ref` cleared, no `buyer_pii` row, and `privacy_requests` recorded one `customers/redact` row with `status:"completed"`, `channel_order_ids:{shopify-1202}`, `counts:{"orders":1,"buyerPii":1,"rawPayloads":0,"personalizedItems":0}`. |
| **EasyPost** — unsigned `POST /webhooks/easypost` | **401** (`{"error":"invalid signature"}`), **and this is the expected result in this dev environment.** `EASYPOST_WEBHOOK_SECRET` is unset in `invai-backend/.env`, so the code falls back to the mock dev secret (`easypostWebhookSecret()` → `MOCK_EASYPOST_WEBHOOK_SECRET`) and verifies against that — the route only 404s when `env.isProd && !env.EASYPOST_WEBHOOK_SECRET` (`api/app.ts:130-134`), which isn't the case here (`NODE_ENV=development`). So an unsigned request correctly fails signature verification (401) rather than being routed away (404); 404 would only be the right answer in a *production* deploy without the secret set, which matches wave 3's own follow-up note ("Decide whether `EASYPOST_WEBHOOK_SECRET` is required in production... for now the route is off without it"). |
| **Stock push** — opt in Shopify connection, adjust stock, worker log shows one `setAvailability` within ~60 s | **Pass.** Toggled "Pause listings when blanks run out" on for the Shopify connection in Settings → Channels (this UI toggle is bound to the contract's `pushAvailability` connection setting — confirmed in the DB: `channel_connections.settings->>'pushAvailability'` went `false → true`). Adjusted stock for Gildan 64000 · White · 2XL (SKU `G64000-WHT-2XL`) from 40 to 25 available via Inventory → Stock → Adjust (toast "Stock updated"). Within seconds the worker log showed exactly one push cycle touching that SKU: `[inventory.jobs] availability planned {...,"connections":1,"variants":2,...}` → `[channels.shopify.mock] mock shopify availability {"connectionId":"fb30690c-...","items":[{"sku":"DB040-G64000-WHT-2XL","available":25},{"sku":"DB035-G64000-WHT-2XL","available":25}]}` → `[inventory.jobs] availability pushed {...,"pushed":2,"skipped":0,"notFound":0,"failed":0}`. That mock log line is `mock.ts:132`'s `setAvailability` implementation (`ChannelAdapter.setAvailability`, confirmed by reading the source) — the two listing variants sharing that blank SKU (`DB040-...` and `DB035-...`) were both pushed once, correctly, with the new quantity (25). |

Screenshot: `gate/1-batch-labels-bought.png` (the only check with a distinct visual state worth
capturing beyond what's already covered by `screens.smoke.spec.ts`'s full-route sweep in section
3; the CSV import, webhook and stock-push checks are API/log-driven per the task and have no
additional screen to capture).

## Failures
None. Every repo check, every E2E suite and every wave 3 smoke check passed on the first attempt.

## Cleanup
- Every process started during this gate was stopped by PID: the original `dev:all` tree (api
  watcher/child, worker watcher/child — including the one orphaned watcher noted above — imaging,
  web, floor, and the `concurrently` wrapper itself), plus the two standalone `pnpm dev:worker`
  restarts used between reseeds. Confirmed after: `ps aux | grep -iE 'tsx|uvicorn|vite|concurrently'`
  and `lsof -iTCP:3000-3199 -iTCP:8000 -iTCP:5173 -iTCP:5174` both empty.
- Infra (Docker) is left running (4/4 containers healthy).
- The dev DB is left freshly reset, migrated (15 migrations) and seeded (360 orders, 148
  listings, 264 shipments). `seed-output.json` has the current station token.
- No extra databases were created or left behind (`\l` shows only `invai`, `invai_test`,
  `postgres`, and the two templates).
- `df -h /`: 14 Gi available (228 Gi total, 46% used) — comfortably above the 5 GB floor, both
  before and after the gate.
- All 7 product repo working trees are clean (`git status --short` empty). No product code was
  edited during this gate — every check was done by driving the running stack (curl, a small
  script using the same oRPC client the E2E suites use, and a real browser), never by touching
  `src/**`.
- This gate's own output — `invai-docs/waves/3/gate.md` and `invai-docs/waves/3/gate/` — is
  committed with a pathspec; the other agents' uncommitted `invai-docs` changes noted above are
  untouched.

## Recommendation
**Push.** Every repo's typecheck/lint/test/build is green, the DB reset/migrate/seed cycle is
clean and reaches migration 0014 as expected with listings confirmed non-empty (T-3-3), the API
golden path is 13/13, the browser golden path plus screens smoke is 15/15 with no console or
request errors on any route, the floor suite is green, and all five wave 3 smoke checks (batch
labels, large CSV via the job path, the three Shopify webhook behaviors, EasyPost's webhook
signature check, and the stock-push round trip to `setAvailability`) pass for real with evidence.
All four cards' reviews are at `approve`. No failures, no flaky tests, no product code touched
during verification.
