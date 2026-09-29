# InvAI v1 QA report

As of Sep 24, 2026, 07:45 CDT. QA / integration engineer (Claude Fable 5.1). Everything below was
run against the real stack on this machine: api :3000 + worker, imaging :8000, web :5173, floor
:5174, a freshly seeded dev database (`pnpm db:reset && pnpm db:migrate && pnpm db:seed`).

## 1. Golden path

Each step was driven twice: through the browser (Playwright, `invai-web/e2e/golden-path.spec.ts`,
tablet steps in `invai-floor/e2e/press.spec.ts`) and through the API alone
(`invai-web/e2e/api-golden-path.spec.ts`). Final runs on a fresh seed: API 13/13, browser 13/13
(steps 1-3 in one run, 4-13 continuing from that state after a locator fix), screens smoke 2/2,
tablet 1/1.

| # | Step | Browser | API | Notes |
|---|---|---|---|---|
| 1 | Owner signs in, Today shows real numbers | pass | pass | Tiles match `today.summary` |
| 2 | Etsy CSV import via Settings > Channels, orders in Orders with ship-by | pass | pass | Fixture `etsy-sold-order-items.csv`: 4 orders, 1 broken row reported, re-import is idempotent (`ordersSkipped`) |
| 3 | Unmapped SKU mapped in the order drawer with "save rule", item ready | pass | pass | Rule saved; "Needs mapping" tab now uses `orders.list.itemState` |
| 4 | Personalized item: proof visible, approve | pass | pass | Proof rendered by the worker after import (imaging `/render/personalization`) |
| 5 | Gang sheets: preview, build, progress, sheet with preview image, utilization >= 80% | pass | pass | Full 22x240 in sheets nest at 88.5-90.7 % (was 51.7 %); a short overflow sheet can be below 80 % and is not judged |
| 6 | Send to vendor; vendor signs in, inbox, acknowledge, printed, shipped | pass | pass | Vendor opens Shops first (accepts the invite per the security follow-up) |
| 7 | Owner marks received, items `transfer_in` | pass | pass | |
| 8 | Floor: station token, PIN 1155, press scan `T:` + `B:`; wrong blank BLOCKED, right blank PRESS, QC pass, pack | pass (tablet suite) | pass | Tablet suite pairs an "any station" tablet (the seeded Press 1 token is pinned to press, so it cannot switch to QC/pack); wrong style -> "Wrong style", wrong size -> "Wrong size" |
| 9 | Shipping: rates, buy label (mock carrier), PDF, tracking push, items shipped | pass | pass | Etsy is a CSV connection, so tracking push resolves to `not_required` (manual upload) rather than `pushed`; the PDF is verified by content type through the API (headless Chromium downloads PDFs instead of rendering them) |
| 10 | Analytics: profit for the order and its design | pass | pass | |
| 11 | AI listing draft (mock) -> Etsy validation -> approve; trademark "Just Do It Nike shirt" -> high | pass | pass | Draft state after generation is `needs_review` |
| 12 | Assistant answers "what was my TikTok margin this week?" (streamed) | pass | pass | Event iterator: `start`, several `text_delta`, `done` |
| 13 | Tenant isolation: a second company sees none of Desert Bloom's data | pass | pass | Orders/designs empty, Today zero, foreign order and sheet ids are NOT_FOUND |

Every web screen (27 routes + order, sheet, design, template and PO detail pages) was opened as the
owner, and the vendor portal as the vendor, with console errors and failed / 4xx-5xx requests
captured: none remain (`e2e/screens.smoke.spec.ts`).

## 2. Bugs found and fixed

Backlog items from v1-plan section 6 are marked with their number.

| Repo | File | Fix |
|---|---|---|
| invai-contracts | `src/schemas/production.ts` | (#15) `wrong_style` added to `MISMATCH_REASONS` |
| invai-backend | `drizzle/0004_print_size_numeric.sql`, `src/db/schema/orders.ts` | (#1) `print_width_in` / `print_height_in` were integer columns; now double precision |
| invai-backend | `src/modules/orders/mapping.ts`, `src/modules/orders/service.ts` | Mapping and artwork overrides no longer `Math.round` inches |
| invai-backend | `src/db/seed/data.ts`, `src/db/seed/index.ts` | (#14) Realistic print-size mix: 10.5x12 adult fronts, 8.5x9.5 youth, 3.75 in left chest, 3x10 sleeves, 12x14 backs, with sample art rendered at those sizes and matching placements; templates 10.5x12 |
| invai-backend | `src/db/seed/index.ts` | (#10) Opening stock now covers every consumed and reserved unit, so no blank has negative on-hand (9 blanks stay under their reorder point on purpose) |
| invai-backend | `src/db/seed/index.ts` | Personalized artwork keys pointed at files that did not exist; the seed renders the 49 proofs through imaging (proofs open, sheets compose) |
| invai-backend | `src/db/seed/index.ts` | Seeded gang sheets pointed at PNG/preview keys that did not exist (broken image, `ERR_BLOCKED_BY_ORB` on the sheet page and in the vendor portal); open sheets are composed for real, received ones keep no file; seeded transfers are laid out from the real sizes |
| invai-backend | `src/modules/production/jobs.ts` | (#3) Production subscribes to `order.cancelled` and scraps the cancelled items' nested transfers (`scrapTransfers`); test in `production.test.ts` |
| invai-backend | `src/modules/production/matcher.ts` | (#15) A different garment style is `wrong_style` (was reported as `wrong_design`) |
| invai-imaging | `app/nesting.py` | Utilization was 52-63 % on the realistic mix: every MaxRects heuristic rotated a 10.5x12 in front into 12 in wide on 22 in film, which nests one per row. Nesting now also tries "upright only" and "most copies across the width" orientation policies and keeps the best; 16 fronts nest two-up at 90.7 % |
| invai-imaging | `app/sample_art.py` | `/sample-art` returned 500 for the "stars" style on tall narrow art (3x10 in sleeve): star band clamped to the width |
| invai-web | `src/features/orders/views.ts` | (#13) "Needs mapping" / "Needs artwork" tabs filter by `itemState` instead of `status: needs_attention` |
| invai-web | `src/routes/_app/orders/index.tsx` | `?q=3310000001` (an order-number search in the URL) was parsed as a JSON number by the router and dropped by `z.string().catch(undefined)`; coerced to a string |
| invai-web | `src/routes/_app/production/stations.tsx` | Stations board recomputed the staff-output query key on every render, so every live update refetched and aborted the previous request (`ERR_ABORTED` in the console) |
| invai-web, invai-floor | `src/i18n/{en,es}.ts`, `src/scan/result.ts`, `src/stations/PressStation.tsx` | (#15) `wrong_style` strings in English and Spanish; the offline press check reports it too |
| invai-floor | `vite.config.ts` | Vitest picked up the Playwright spec; tests are limited to `src/**/*.test.*` |

Commits (branch `platform-v1`, nothing pushed): contracts `a5e7f45`; backend `a061c46`,
`4b99635`; imaging `951228d`; floor `9e7d239`, `48a6a27`; web `2c25ac4` + the E2E follow-up.
Backend commits touch only QA-owned paths; the security reviewer's migration `0005` sits on top of
`0004_print_size_numeric` in the journal, and `db:reset && db:migrate && db:seed` runs clean from
scratch.

## 3. Remaining known issues (by severity)

1. **Intermittent 403 on the browser's presigned CSV upload** (medium). Twice in ~10 runs MinIO
   answered `SignatureDoesNotMatch` to the browser's PUT while the same upload passed seconds
   later and always passes from Node. The signature now binds `content-length` (security review,
   `src/lib/s3.ts` `presignPut`); a browser that omits or changes that header would fail exactly
   this way. Not reproduced under instrumentation. The E2E logs the storage error body and retries
   the import once. Suggested hardening (reviewer's file, not changed): stop signing
   `content-length` and enforce the size with `headObject` after the upload.
2. **A presser cannot use the Quality check or Pack stations from a press-kind tablet** (low, by
   design). Station kind is fixed per token; only "Any station" tablets switch. The seed only
   issues a "Press 1" token, so a demo of QC/pack on the tablet needs a token from Settings >
   Stations for QC 1 / Pack 1 (or an any-kind station). The tablet suite pairs one through the API.
3. **`blanks.list` needs `catalog.read`, which pressers lack** (low). The floor app does not call
   it, but any future floor screen that looks up blanks by code will need `auth: "floor"` plus a
   permission pressers have.
4. **Etsy/Amazon/TikTok/Walmart tracking push is `not_required`** (accepted for v1). Only the
   Shopify (mock) adapter pushes; CSV channels point the user at a manual upload.
5. **Short overflow sheets can nest below 80 %** (cosmetic). The last sheet of a batch holds the
   leftovers (12-88 in long); the E2E only judges sheets of 100 in or more.
6. Backlog items left open as accepted in v1-plan: #11 (AI publish falls back to CSV), #12
   (`get_production_status` tool name), #16 (vendor accept flow is "open the shop list"), #17
   (`blankReusable` on QC fail), #18 (restart processes before E2E).
7. Worker log noise after a process restart: BullMQ "could not renew lock" for a
   `finance.recompute` job interrupted by the restart, and `catalog.runDesignQa` retries that
   failed against imaging while it was being restarted. Both clear on their own.

## 4. How to run the E2E suites

```
# infra + api + worker + imaging + web + floor (or invai-infra/scripts/dev.sh)
cd invai-backend && pnpm db:reset && pnpm db:migrate && pnpm db:seed   # imaging must be up: the seed renders art

cd invai-web
pnpm e2e                                   # browser golden path + every-screen smoke (chromium, ~1 min)
E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts   # API-only golden path (~10 s); run on a fresh seed, it
                                                  # consumes the same imported orders as the browser path
pnpm e2e:ui                                # Playwright UI mode

cd invai-floor
pnpm e2e                                   # tablet: pair, PIN, press scan check, QC pass, pack (~3 s)
```

- Both golden paths expect a **freshly seeded** database; the browser one tolerates a re-run on
  the same database (steps already done are skipped and verified through the API).
- Playwright needs the Chromium build matching `@playwright/test` (`pnpm exec playwright install
  chromium` once). Reports land in `e2e/.report`, traces and screenshots of failures in
  `e2e/.results` (both git-ignored).
- `E2E_WEB_URL`, `E2E_API_URL`, `E2E_FLOOR_URL` override the default local ports.
- Helpers: `invai-web/e2e/helpers/api.ts` (cookie session + typed oRPC client, station and floor
  sessions, uploads, polling), `invai-web/e2e/helpers/ui.ts` (login, console/request watcher),
  `invai-floor/e2e/helpers/api.ts`.

## 5. Repo checks at hand-off

`pnpm typecheck && pnpm lint && pnpm test` pass in contracts (31 tests), ui (20), backend (148),
web (23, plus `pnpm build`) and floor (41, plus `pnpm build`); imaging `uv run ruff check . && uv run
pytest` (27). The dev database was reset, migrated and seeded last, and every app process was
stopped; only the Docker infra (Postgres, Valkey, MinIO, Mailpit) is left running.

## 6. Wave 18: market signals (acceptance tests first, 2026-09-27)

Written before the build from `specs/market-signals.md` AC1–AC33 (`waves/18/reports/QA-acceptance.md`
has the AC → test table). All QA-owned; implementers don't edit them.

| Suite | File | Tests | State on 2026-09-27 (first pass) | State on 2026-09-27 (second pass, at HEAD `0fce415`) |
|---|---|---|---|---|
| Market module (T-18-3) | `invai-backend/src/modules/market/market.acceptance.test.ts` | 25 (22 + AC18's 2 new) | red: `./jobs` missing (5 run against the stub and fail "not implemented") | **green (25/25)**, alone or with the other 3 market files in one run |
| Mock rule in production (AC22, AC29) | `invai-backend/src/modules/market/market-prod-mode.acceptance.test.ts` | 3 | red: `./jobs` missing | **green (3/3)** |
| Provider outage (AC20) | `invai-backend/src/modules/market/market-outage.acceptance.test.ts` | 3 | red: `./jobs` missing | **green (3/3) alone or with `market-prod-mode`**; red 1/3 when run in the same `vitest run` after the other two market files (below) |
| Assistant market tools (T-18-4) | `invai-backend/src/modules/ai/market.acceptance.test.ts` | 9 | red: `../market/jobs` missing | **green (9/9)** |
| Browser: chips, badge, votes, niche chip (T-18-5) | `invai-web/e2e/market.spec.ts` | 5 | not yet run (needs the stack with market jobs run) | not yet run in this pass (needs the running stack; T-18-5 not landed as of this pass) |

### Second pass (2026-09-27, at backend HEAD `0fce415`)
Fixed in my fixtures (not product code), each run standalone with `TEST_DATABASE_URL=…/invai_t18_qa`,
`REDIS_URL=redis://localhost:6379/15`:
- **AC26/AC30 dollars-vs-cents**: `product()`'s `prices` field is `Cents` (`c2057df`); 7 call sites
  across both files stored a dollar-shaped number (`24.99`, or `P0 / 100`) instead of the integer
  cents. Fixed all 7 (`market.acceptance.test.ts` lines formerly 537/818/925/1083/1160/1211/1243,
  `ai/market.acceptance.test.ts` lines formerly 407/414/539).
- **AC17 the "last complete ISO week" was empty for a Tuesday `now`**: the `-3 days` fixed offset in
  `sale()`/`weeklySales()` only lands `weeksAgo` in its intended ISO week when `now`'s ISO weekday is
  Thursday-Sunday; for Monday-Wednesday it lands one week early, so `weeklySales(N, …)` populated
  real weeks 2..N+1, not 1..N, and the true most recent complete week had 0 sales. Fixed with a
  weekday-aware offset (`isoWeekday(now) - 4`, i.e. always mid-week of the intended ISO week) in both
  files' `sale()`/`weeklySales()`; the "AC17 (hand SQL)" companion test now gets its window from
  `completeWeeks()` itself instead of a second hand-rolled offset. Verified: AC17's `yoy` assertion
  (12/12 - 1 = 0) now holds by direct computation, not luck.
- **AC19, per the tech lead's decision** (`waves/18/wave.md` round log, 2026-09-27): rewritten to
  assert on `filterComparables` (the normalize step, `./signals`) applied to the stored
  `market_price_snapshots` row `getPricePosition` actually reads, not on the provider's raw output
  (which is a deliberate mix per T-18-2 round 2). Needed a `listing()` + `product()` for the
  personalized design in `beforeAll` (T-18-3's `refreshPricing` only fetches a price snapshot for a
  design with an active listing on the channel).
- **AC18 written** (`market.acceptance.test.ts`, new describe block): a pure `fitTrend` proof that a
  null (out-of-stock) week shrinks the fit window while a same-value 0 counts as a real zero-sales
  week, plus an end-to-end case (a blank with a reconstructed 2-week stockout via `inventoryMovements`
  `receive`/`consume` rows) asserting the trend stays "flat" (not "insufficient" or "falling") and
  `market_signals.value.outOfStockWeeks` is 2. The "R1 names the blank and links to reorder" half of
  AC18 is already covered by AC3's `blankBelowReorderPoint` assertion.
- **Two bugs found only once the price bug was fixed** (both fixture-only, found by re-running after
  the AC26/AC30 fix let the tests run further than before):
  - `THIN_COSTS`/`THIN` (both files): `market/compute.ts`'s margin signal never reads
    `channelFeesCents` from `profitLines`; it recomputes the channel fee fresh from the default fee
    schedule (Amazon apparel referral: 5% under $20). At the original $12.99/`fees:195` the *real*
    margin came out ~29%, above the R2 threshold, so R2 never fired even with the cents fix. Lowered
    the design price to $10.00 and rebalanced the absolute-cost fields (`blank/transfer/label/
    packaging/labor`) to land at the intended ~19% under the *real* fee, and to keep the R2
    test-price ceiling (`p0 × 1.1`) safely under the mock's own $12.00 comparable floor (a second,
    independent reason R2 could fail to fire at $12.99 depending on the mock's per-ref random
    median).
  - `profitFor()` (`market.acceptance.test.ts`): AC26 calls it twice for the same design (once in
    `thinAmazonDesign`, once after a day-by-day sales loop); the second call re-inserted profit
    lines for items the first call had already covered, hitting `profit_lines_company_id_order_item_id_index`.
    Added `.onConflictDoNothing()` on `(companyId, orderItemId)`. Only surfaced once the AC26 test
    finally reached that line (previously it returned early on the undefined R2).
  - `thinAmazonDesign`'s design also needed `runMarketJob(JOB.refreshPricing, …)` before
    `computeSignals` in the AC26 test: `moose` is created mid-test, after `beforeAll`'s
    `runShopJobs`, so its price-position snapshot was never fetched.

**Cross-file interaction, not fixed (filed, not a fixture bug)**: `market-outage.acceptance.test.ts`
passes alone or paired with `market-prod-mode.acceptance.test.ts`, but its `AC20` "older asOf" check
went red once when run in the same `vitest run` as `market.acceptance.test.ts` and
`ai/market.acceptance.test.ts` first. Cause: `market_series_cache` (ADR 0015) has no `company_id` by
design, so `refreshDemand({})` calls from *different test files*, each frozen at a different `now`,
upsert the *same* global cache rows; whichever file's `refreshDemand` call lands last in real
wall-clock execution order wins the row, regardless of that file's own simulated calendar date. This
is a real test-isolation gap in a global, cross-tenant table, not something a QA fixture can fix by
itself. Filed to the tech lead for T-18-2/T-18-3 (owner: backend-engineer/architect, per ADR 0015);
not reproduced when each acceptance file is run on its own test DB per its own card, which is how
this pass verified all four green.

Run the backend suites on your own test DB, never the shared one:
```
cd invai-backend
TEST_DATABASE_URL=postgres://invai_app:invai@localhost:5432/invai_t18_qa \
TEST_MIGRATION_DATABASE_URL=postgres://invai:invai@localhost:5432/invai_t18_qa \
REDIS_URL=redis://localhost:6379/15 \
node_modules/.bin/vitest run src/modules/market src/modules/ai/market.acceptance.test.ts
cd invai-web && pnpm e2e e2e/market.spec.ts     # seeded stack, market jobs run, web on :5173
```

AC18 (blank out-of-stock weeks excluded from the trend fit) was written in the second pass (below),
once T-18-3's history schema existed. AC28 is a separate scale run (below). Held-back cases are kept
outside the repos and added after each author reports done.

### AC28 scale run — ran 2026-09-28 (wave 19 gate): PASS
- `MARKET_SCALE=1 pnpm exec vitest run src/modules/market/market-scale.acceptance.test.ts` (QA file,
  opt-in) on its own DB `invai_t19_qa_scale`; SHAs contracts `83eee25`, backend `53cc86a`.
- Fixture: 5,000 active designs, 584,000 orders / 1,168,000 items over 156 weeks (≈1,070 units/day,
  Q4 skew for a fifth of the catalog), 96,264 profit lines (90 d), Etsy + Amazon connected, mock
  sources; built in 40.4 s.
- `refreshDemand` 4.4 s; `computeSignalsForShop` 7.8 s (5,000 designs mapped by stems, 15,470
  signals, 0 recommendations on the uniform series); re-run 7.5 s, 0 new recommendations. Budget
  15 min. Comparable to T-18-3's own 12.2 s synthetic run (its scratchpad fixture is gone; this file
  makes it repeatable). k6 tool-latency and EXPLAIN parts of the plan below are still open.

Original plan:
- Profile: `large` per `scale-test/profiles.md`: 5,000 active designs, 1,000 orders/day, 3 years of
  weekly history, niches skewed like a real catalog (60% evergreen, 25% holidays, 15% unclassified),
  Amazon and Etsy connections, mock outside sources. Seeded into a separate database
  (`invai_t18_scale`), never the shared dev DB; location of the profile agreed with backend-foundation
  (`invai-backend/src/db/seed/scale/`, backlog B-34).
- Measures: `market.computeSignals` wall time for the shop (target ≤ 15 min on this machine, T-18-3
  AC15 gives the smaller synthetic timing), and p95 of each market tool (`get_market_trend`,
  `get_seasonality`, `get_price_position`, `simulate_price`) under a k6 `constant-arrival-rate` of
  2 req/s for 5 min against a `PORT=3161` API (target p95 < 500 ms, ≤ 20 rows each). EXPLAIN
  (ANALYZE, BUFFERS) as `invai_app` on the signal and recommendation reads for the large tenant and
  a small one (indexes lead with `company_id`).
- Report: this section (profile, SHAs, p50/p95/p99, break point, EXPLAIN findings, filed cards).

## 7. Wave 19: weekly digest (acceptance tests first, 2026-09-27)

First pass, written from `invai-docs/specs/weekly-digest.md` before T-19-1 (contract) and T-19-3
(digest module) land. Contract 0.7.0 hadn't landed at write time either, so tests call the
*existing* top-level router by path (`digest.*` procedures aren't on it yet) and load
`src/modules/digest/jobs.ts` (doesn't exist) through a dynamic `import()` on a path constant, the
same trick wave 18's `market.acceptance.test.ts` used — the file typechecks today, and each test
fails on the missing job/procedure with one clear reason, not a typo. AC14-17 and AC31 (Market
watch) run against wave 18's real, pushed `market/service.ts` (`listDigestMarketItems`,
`recordRecommendationsShown`) instead of a stub, so once T-19-3 lands, only the digest half needs
reconciling.

Files (all QA-owned, `invai-backend/src/modules/digest/*.acceptance.test.ts`):
- `digest.acceptance.test.ts` — AC1, AC2, AC4-13, AC18, AC27, AC28, AC30 (17 cases); AC3 (DST) is
  `it.fails` since a full DST harness needs T-19-3's own week-boundary function, not just a frozen
  clock; AC21 is `it.todo` until a credit-ledger-draining helper exists (T-19-2).
- `digest-market.acceptance.test.ts` — AC14-17 (4 cases).
- `digest-prod-mode.acceptance.test.ts` — AC31, mock visibility rule in production (1 case, `env`
  mocked to `isProd: true` like wave 18's `market-prod-mode.acceptance.test.ts`).
- `digest-consent.acceptance.test.ts` — AC23-26 (email/consent/unsubscribe; T-19-3's own AC9 names
  AC23/AC26, T-19-4's card names AC24/AC25), loading `src/lib/notify.ts` / `src/lib/links.ts`
  (don't exist yet) the same way, and exercising the public `/l/:token` routes through the real
  Hono `app` (`../../api/app`, exists today) with `app.request(...)` — they 404 until T-19-4 mounts
  them, a clean expected-red reason with no dynamic-import indirection needed.
- `invai-web/e2e/digest.spec.ts` — one browser spec: Today card, digest page in English and in
  Spanish at 390px, Settings → Notifications (AC33's shadow-mode explanation, office refused),
  account toggle, the public unsubscribe page. Every case is `test.fail`-marked; `/digests` and
  `/unsubscribe` don't exist yet, so navigation itself fails today. Not run against a live stack
  (no page exists yet to serve it); typecheck and Biome are clean.

Result on a first run (own test DB, fresh, `invai_t19_qa`):
```
Test Files  4 failed (4)
     Tests  24 failed | 1 expected fail | 1 todo (26)
```
Every failure is `Cannot find module '.../digest/jobs'` (or `'.../lib/notify'`), or `procedure
digest.X is not on the router (T-19-3/T-19-1 router.ts)` — the right reason, not a fixture bug.

**Update (same day, T-19-1 landed mid-session, contract 0.7.0):** re-aligned all four backend files
to the real `Digest`/`DigestSummary`/`DigestInsight` shapes (`marketWatch` not `market`, `planUsage`
not `plan`, `net.value` not `glance.netCents`, `partialChannels` not `glance.partial`), imported the
real types from `@invai/contracts`, and fixed AC17 to vote through `market.recommendations.vote`
(per the contract's own doc comment — a Market watch vote is the shared market-signals record, never
`digest.feedback`) and AC13 to test what the contract actually returns (`formatted.{en,es}` on every
fact) rather than a server-rendered string that was never part of the design. T-19-3's day-1 stub
(router + job registration placeholder) also landed mid-session: re-ran the suite against it and
confirmed the permission guards already return `FORBIDDEN` correctly for presser/office before
hitting the "not implemented"/"job not registered" wall — still 24 failed | 1 expected fail | 1 todo,
same count, now failing one layer deeper (job not registered, not router-missing) and for the
right reason at each point checked.

Known assumptions to reconcile once T-19-3/T-19-4's full build (not just the day-1 stub) lands
(flagged in each file's header, not hidden):
- Job names `digest.sweep` / `digest.build` are QA's best guess (wave.md fixes router names, not
  job names). If the real names differ, the fix is a one-line rename in these test files, done by
  QA, not the implementer.
- `channel_connections.disconnectedAt` (used by the AC7/D1 fixture) is a guessed column name; if
  D1's "disconnected during the week" signal lives elsewhere (a status-change log, an event), the
  fixture helper needs a small rewrite once T-19-3's schema is visible.
- AC1's "the seed" is treated as a fixture shop built in-test with explicit `placedAt`s, per the
  spec's own "Seed vs fixture rule" (not the literal `pnpm db:seed` output).

### Held-back cases (kept outside the repos, added after T-19-3/T-19-4 report done)
See `.claude/agent-memory/qa-engineer/held-back/T-19-3.md` and `T-19-4.md`:
- A second sweep run with the shop's `hour` changed *between* the two runs (does the new hour apply
  to a digest already `ready` for that week, or only future weeks — AC5 doesn't say).
- A digest built, then the order it counted gets refunded after the fact (spec: "out of scope,
  re-sending an email"; the acceptance case checks the *stored* digest doesn't silently change).
- Two people in the same shop, one opted in before the digest existed and one after — both must get
  exactly one email, not zero and not two (AC2/AC23 boundary).
- A tampered token where only the `ref` field changes (not company/user) — must still 4xx, not
  silently unsubscribe from the wrong kind.
- Office user with `finance.read` revoked mid-week (role change) — must not receive next week's
  email even though last week's preference was on.

### Second pass (2026-09-28, at backend HEAD `776697b` / T-19-3 `cadc338`+`bef6158`, web HEAD `9b8a69e`)
Fixed in my fixtures (not product code), backend files each run standalone on `TEST_DATABASE_URL=…/
invai_t19_qa`, `REDIS_URL=redis://localhost:6379/15`:
- **`mondayPhoenix(d)` offset, every file** (T-19-3's own report flagged this): the helper returns
  shop-local **midnight** (07:00Z), not 07:00 local, so every `freeze(monday + 5min)` landed at
  00:05 local — before the default 06:00-10:00 build window — and every `digest.get` after it was
  `NOT_FOUND` for the wrong reason. Fixed all 18 occurrences across `digest.acceptance.test.ts`,
  `digest-market.acceptance.test.ts` and `digest-prod-mode.acceptance.test.ts` to `+7h5m`.
- **AC3 (DST) fixture had no sale**: the `it.fails` case built `skipped_quiet` (zero orders), not
  the DST-off-by-an-hour failure it claimed to prove; added a sale inside the target week, confirmed
  it now genuinely passes with `it` (not `.fails`), and removed the marker.
- **AC10's net check used the wrong field and formula**: `Digest` has no `glance.netCents` (fixed to
  the top-level `net.value`, contract 0.7.0), and `finance/profit.ts`'s `finalize()` computes net as
  revenue minus every cost-bucket column — it never reads a profit line's cached `netCents` back for
  aggregation (the same rule that already bit wave 18's market fee signal). Added a `costCents`
  fixture option (stored as `blankCostCents`) and rewrote the reprint case as a free reprint
  (`revenueCents:0, costCents:500` → net -500) instead of relying on a chosen `netCents`.
- **AC18's weekKey was off by one**: `mondayPhoenix("2026-12-07")`'s last complete week is `2026-W49`
  (verified against `week.ts`'s real `lastCompleteWeek`), not `2026-W50`.
- **AC27/AC28 used the global sweep where a targeted build was needed**: the sweep also builds every
  other due shop's own (quiet) digest for the same week, so `other`'s/`b`'s `digest.get`/`digest.list`
  weren't actually empty for the reason the test claimed. Switched both to `digest.build` targeted at
  the one company under test.
- **AC30 had no digest built at all** before hammering `digest.sendPreview` three times, so the first
  call answered `NO_DIGEST`, not `OK`, and the rate-limit assertion never got exercised for the real
  reason. Added a build step first.
- **AC14/AC15/AC16/AC17 (Market watch) had zero orders**: `build.ts`'s `isQuiet` gate skips
  `marketOf(...)` entirely for a zero-order week, so every one of these shops built `skipped_quiet`
  and Market watch was never evaluated — the assertions on AC14/AC16/AC17 either failed outright or
  (AC15) passed by accident, since its own assertion doesn't require Market watch to be populated.
  Added a minimal sale to each.
- **AC17 additionally depended on the real wall-clock date**: `listDigestMarketItems` only shows
  recommendations created within 7 days of the build instant; the fixture's default `createdAt: new
  Date()` only fell inside that window because the *actual* run date happened to be close to the
  target week — true for AC14 (run date 2026-09-27, target week ending 2026-09-28) but not for AC17
  (target week ending 2026-10-19). Gave every recommendation in AC14/15/17 an explicit `createdAt`
  inside the target week so the suite no longer depends on when it happens to run.
- **AC31 (prod mock filter) had the same "zero orders" and "no counter-example" problems**: no sale
  (so the week was always `skipped_quiet`, proving nothing about the mock filter specifically) and no
  non-mock recommendation that should still show (so a completely broken filter would have looked
  identical to a working one). Added a sale and a second, non-mock recommendation; the assertion now
  proves the filter drops the mock item specifically.

Result after fixes, run standalone twice on a fresh `invai_t19_qa`/Redis 15 (determinism check):
```
Test Files  4 passed (4)
     Tests  25 passed | 1 todo (26)
```
AC21 stays `it.todo` (needs T-19-2's credit-ledger-draining helper, unrelated to this pass).

**`invai-web/e2e/digest.spec.ts`**: T-19-5 landed (`9b8a69e`) by the time this pass ran, so every
`test.fail()` marker was removed and the suite was run for real against my own stack (API `:3162` on
a migrated dev-DB copy, `digest.build` forced for Desert Bloom Tees `2026-W39`; web built with
`VITE_API_URL=http://localhost:3162` and served with `vite preview`, on `:4417`). Three real fixture
bugs found and fixed the same way (wrong click target/locator, not the wrong behavior):
- "Today card" clicked the headline paragraph, which isn't inside the link; the real link is a
  sibling "See this week" — fixed to click that.
- The digest-list row's accessible name is a formatted date ("Week of Mon, Sep 21…"), not the raw
  ISO week key, in either language — matched by `a[href^="/digests/"]` instead.
- "office cannot see Notifications" expected a non-200 HTTP status; a client-rendered SPA route
  always answers the navigation itself with 200, then the guard renders the refusal after the oRPC
  call returns — reworded to check the settings form never renders.
- "invalid token" navigated with a garbage `?token=`, which shows the normal confirm state until
  someone clicks Unsubscribe; the real invalid-link state is what the backend's GET redirect
  produces for a mangled token (`?error=invalid`) — fixed to reproduce that directly.

**Bug found and filed, not fixed (not my path)**: the "office cannot see Notifications" refusal
currently renders the raw backend string verbatim and untranslated — "Missing permission org.manage
for digest.settings.get" — because `invai-web/src/lib/errors.ts`'s `errorInfo()` has no `FORBIDDEN`
case (falls through to the server's own message, `invai-backend/src/api/orpc.ts:128`). This is a
pre-existing, cross-cutting gap (not introduced by T-19-5), but T-19-5's Notifications screen is the
first real user path in this wave to surface it. Filed to the tech lead for web-engineer
(`src/lib/errors.ts`): add a `FORBIDDEN` case with a plain-language, translated message, same shape
as the existing `NOT_IMPLEMENTED`/`EMAIL_NOT_VERIFIED` cases.

**Environment note for whoever runs this next**: `invai-web`'s `dist/` is a shared, gitignored build
output directory — another agent rebuilding it (a different `VITE_API_URL`) mid-session silently
redirected my browser's own API calls to their backend, since `VITE_API_URL` is baked in at build
time and only affects the bundle, not `E2E_API_URL`/`E2E_WEB_URL` (those only steer Playwright's own
`baseURL` and the `Session` helper). Build to an isolated `--outDir` (e.g. `dist-qa<port>`) and serve
that with `vite preview --outDir dist-qa<port>` instead of the shared `dist/`.

Result, `invai-web/e2e/digest.spec.ts` against the isolated stack:
```
8 passed (18.3s)
```

### AC29 scale run — ran 2026-09-28 (wave 19 gate): PASS
- `DIGEST_SCALE=1 pnpm exec vitest run src/modules/digest/scale.test.ts` (T-19-3's opt-in file) on
  `invai_t19_qa_scale`; SHAs contracts `83eee25`, backend `53cc86a`.
- One 1,000-orders/day shop (63,000 orders): `buildDigest` **330 ms**, `ready` (budget 60 s).
- Sweep over 1,000 Phoenix shops all due Mon 07:05: **15.2 s**, 1,000 built, 0 failed; the second
  sweep built 0 (no duplicate digest) (budget 30 min). The sweep builds shops in turn inside one
  job, so there was no BullMQ fan-out to watch. Full details: `waves/19/reviews/gate.md` §6.

Original plan:
- Profile: reuse wave 18's `large` scale profile where possible (same seed location,
  `invai-backend/src/db/seed/scale/`, backlog B-34), extended with a `weekly-digest`-shaped set of
  1,000 small/mid shops all due in the same local hour (skewed time zones so the hourly sweep has
  real concurrent work), plus one `large` shop at 1,000 orders/day for the single-build timing.
- Measures: the hourly sweep over 1,000 due shops completes within 30 minutes with no duplicate
  digest (spec AC29); the single large shop's build completes within 60 seconds (T-19-3's own
  smaller synthetic check covers the shape of this, not the full 1,000-shop concurrency). Watch
  BullMQ waiting count and oldest-job age on the digest queue during the run, and Postgres
  connections (the sweep fans out one build job per due shop).
- Report: this section (profile, SHA, sweep wall time, duplicate count, build p50/p95 for the large
  shop, any queue backlog, filed bottlenecks) once T-19-3 reports done.

## 8. Wave 20: side-effect and live-adapter tests (B-71, T-20-3, 2026-09-28)

Backend HEAD `5a443ed`. New files are QA-owned `*.acceptance.test.ts`; they run with the normal suite
(`pnpm test`), on `invai_t20_3` during the card. All 27 new tests pass on a fresh DB and on a second run of
the same DB (unique data per run); the seven files together take about 7 s (budget < 60 s).

### AC1: coverage inventory ("one effect on retry / crash between the outside call and the commit")

| Side effect | Existing proof (file:line) | Gap the new tests close |
|---|---|---|
| `buyLabel` | `modules/shipping/label-safety.test.ts:286` (commit failure after the carrier charged never buys twice), `:307` (crash mid-call: retry blocked while in flight, then read back), `:365` (unknown outcome stays `buying`, retry reads back); `jobs.test.ts:468` (sold but unrecorded → read back) | concurrent double buy; a second request while the carrier call is still open; the real EasyPost REST adapter through the crash |
| `rateOrder` | `label-safety.test.ts:204` (rating again reuses the open shipment). No outside effect to duplicate (rating charges nothing), so "crash before commit" is not a money case | concurrent double rate → one shipment row, one quote set |
| `voidShipment` | `push-void.test.ts:436` (commit failure after the carrier refunded never refunds twice); `jobs.test.ts:498` (stuck void read back and finished) | concurrent double void; a second void while the carrier call is open |
| `batchBuy` | `batch.test.ts:204` (crash mid-buy: the restarted run reads the carrier back, never buys twice); `:155` (a duplicate run of the job buys nothing) | two batches over the same orders at once: one label per order, each credited to one batch |
| `pushTracking` (Shopify) | `push-void.test.ts:235` (commit failure after the channel took it never notifies the buyer twice); `jobs.test.ts:514` (stuck push sent once) | concurrent double push; the real Admin GraphQL adapter through the crash (read-back = fulfillment orders) |
| `pushTracking` (CSV) | `push-void.test.ts:413` ("CSV-only channels": `not_required`, units ship on the carrier scan) | the CSV channel never reaches a channel adapter, however often it is pushed |
| `syncAvailability` | `inventory/availability.test.ts:313` (a retry after a **failed** call resends under the same key). **none** for a crash after the channel accepted the push | crash after the channel took the push → retry under the same key, quantity stored once; two concurrent runs carry one key |
| `publishDraft` | **none** | publishing twice, or twice at once, leaves one file at one key and the draft approved; another tenant gets `NOT_FOUND` and no file |
| `renderItemArtwork` | `personalization/render-job.test.ts:157` (the job renders once). **none** for a crash between the render and the commit | crash after imaging rendered leaves `pending`, retry saves once; two concurrent renders → one row, one `artwork.rendered`; the interactive re-render keeps one row |
| `submitPo` | `inventory/po-safety.test.ts:251` (commit failure after the supplier accepted never orders twice), `:272` (crash mid-call), `:321` (unknown outcome) | concurrent double submit; the real S&S REST adapter through the crash |
| `receivePo` | `po-safety.test.ts:336` (a retried receipt counts once; a changed retry is `CONFLICT`) | concurrent double receipt under one key counts the stock once |

### AC2/AC3: the new files (criterion → file → test)

| File | Tests | What it proves |
|---|---|---|
| `modules/shipping/side-effects.acceptance.test.ts` | 8 | rate ×2 → one row; buy ×2 → one charge, loser `CONFLICT` or stored label; buy while open → refused before any carrier call; void ×2 and void while open → one refund; batchBuy ×2 batches → one label per order, credited once; push ×2 → one channel call, units ship once; CSV push → no adapter |
| `modules/inventory/side-effects.acceptance.test.ts` | 4 | submit ×2 → one order, loser `CONFLICT`; receipt ×2 under one key → +4 once; availability crash after the call → same key on retry, stored once; two runs → one key |
| `modules/ai/publish.acceptance.test.ts` | 3 | publish ×2 and ×2 at once → one object, one key, draft approved; other tenant `NOT_FOUND`, no file |
| `modules/personalization/render.acceptance.test.ts` | 3 | crash after render → `pending`, retry saves once; concurrent → one row, one event; re-render keeps one row |
| `integrations/carriers/easypost-live.acceptance.test.ts` | 2 | real adapter over stubbed `fetch`: `POST /shipments` with our id as `reference` and Basic auth; `POST /shipments/{id}/buy` once through a commit failure, retry is `GET /shipments/{id}` (never `/buy`); a `/buy` timeout is unknown → read back; signed `tracker.updated` → `in_transit` → `delivered`, redelivery acknowledged as duplicate |
| `integrations/channels/shopify-live.acceptance.test.ts` | 3 | orders poll: 429 → backoff ≥ 1 s, then `pageInfo` paging with `after`; every call `POST …/graphql.json` with the token header present (value never asserted, never in the URL); `FulfillmentOrders` then one `fulfillmentCreate` (`notifyCustomer: true`) through a commit failure; retry reads back, no second create; a `userError` leaves the push `pending` and retryable |
| `integrations/suppliers/ss-live.acceptance.test.ts` | 4 | tenant credentials pick the live adapter; `POST /v2/orders/` with Basic auth, `poNumber`, `rejectLineErrors: true`, key never in URL/body; retry after a commit failure is `GET /v2/orders/{poNo}`; `POST` timeout → read back; 400 → `SUPPLIER_REJECTED`, PO back to `draft` |

Fixtures are seed-shaped (`Desert Bloom Tees`, `Test Buyer`, `1 Buyer Way, Brooklyn NY 11201`,
`buyer@example.com`, carrier-shaped fake tracking codes, `pl_t203_*`/`shp_t203_*` ids); no real data was used,
so nothing was scrubbed.

### Regression proofs (worktree `../invai-backend-t20-3` at `5a443ed`, each guard removed, then restored)

| Guard removed (product code, worktree only) | Test that went red |
|---|---|
| EasyPost `reference: req.shipmentId` → `null` | easypost-live "rates, buys once through a crash…" (`toMatchObject` on `reference`) |
| EasyPost `lookup()` returns nothing (retry can't read back) | both easypost-live tests (retry re-`POST`s `/buy`; timeout case "couldn't confirm") |
| S&S `rejectLineErrors: true` → `false` | ss-live "orders once through a crash…" |
| `submitPo` retry never calls `findOrder` | ss-live crash and timeout tests (`POST` instead of `GET`) |
| `submitPo` in-flight `CONFLICT` off | inventory "concurrent double submit" (2 supplier calls) |
| `receivePo` ignores `idempotencyKey` | inventory "concurrent double receipt" (+8, not +4) |
| availability push sends a fresh key per attempt | both inventory availability tests |
| `publishDraft` key per attempt (random) | both ai publish tests (2 objects) |
| artwork always inserted (no upsert) | all 3 personalization tests |
| Shopify token header dropped | shopify-live poll and push tests |
| Shopify 429 gives up instead of backing off | shopify-live poll test |
| Shopify "nothing left to fulfill" → failure | shopify-live push test (`retry` instead of `pushed`) |
| `buyLabel` in-flight `CONFLICT` off | shipping "buy while the carrier call is open" (2 carrier calls) |
| `pushTracking` in-flight busy check off | shipping "concurrent double push" (2 channel calls) |
| `voidShipment` in-flight `CONFLICT` off | shipping "void while the carrier call is open" (2 carrier calls) |

Note: removing only Shopify's `remainingQuantity > 0` filter did **not** fail the push test, because the
fulfillment order's `CLOSED` status is a second layer of the same read-back. The "nothing left" mutation is
the one that proves the retry path.

### AC4: bugs found
None. Every guard the card names exists and holds; no test was left failing.

## 9. Wave 20 gate (2026-09-29, `invai-docs/waves/20/reviews/gate.md`)

Fresh seed built **with two workers running** (T-20-5: `queues obliterated in /0`, no unique violations, no negative stock). API golden path 13/13 (11.6 s, my API `:3190`), floor 3/3 (8.8 s), full browser run 35/35 (1.7 m, `:5173` → `:3000`, "No screen issues"). Digest `2026-W39` built by the sweep on a Tuesday (in-app only: `quiet_hours`), `+2.8 pts` / `unchanged` / `sin cambio`, `Semana del lun 21 de sep`, no past act-by in Market watch, Today alert `Ship-by was Sep 25 and no label has been bought.`, office@ refused page translated.

Filed (details and owners in the gate file): **High** the production CSP `connect-src 'self' <api>` blocks the browser's presigned PUT to S3/MinIO (CSV import spins forever under `vite preview`; `pnpm dev` hides it) [web-engineer, security co-review]; **Medium** on a fresh seed with a worker running, `market.sweep` treats the day as done after the outbox-triggered `computeSignals` and never enqueues `refreshDemand`, so no outside mock sources, no `Sample data` badge and `market.spec.ts:91` red until 03:00 UTC [backend-engineer market]; **Medium** the assistant seasonality answer still prints `Act by 2026-08-04 … Act now` for an under-way peak (`assistant-tools.ts:1026`) [ai-engineer]; **Low** Spanish digest action chips `~704,47 US$` next to es-US numbers [web-engineer]; **Low** `src/db/seed/outbox-hold.test.ts` flaky under load, shared `companyId` with no cleanup cascades [backend-foundation]. QA fixed its own `e2e/digest-dates.spec.ts` AC1 race (wait for the route change after the row click).

Suite notes: the full browser run makes 16 sign-ins in ~40 s against the 20/min per-IP Redis-shared bucket (decision 0008): don't run another suite or curl sign-ins in the same minute. The floor helper hard-codes `origin: http://localhost:5173`, so the floor suite only runs against an API whose `WEB_ORIGIN` is `:5173`.
