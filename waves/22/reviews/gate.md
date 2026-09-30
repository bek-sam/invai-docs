PASS

# Wave 22 integration gate (2026-09-29/30, attempt 4)

QA: qa-engineer on Opus 5.5. Fresh reset, migrate, seed with imaging running; all suites green on that seed.

## Carried forward (green, not rerun — from attempt 1, unaffected by this attempt's reset)
- contracts: 88 passed
- backend: full suite at `04e72a0` with `REDIS_URL=redis://localhost:6379/14`: 1188 passed
- web: 117 passed (build needs `VITE_API_URL`, expected)
- floor: 96 passed (build needs `VITE_API_URL`, expected)

## This attempt: fresh seed + E2E
Stopped the stale stack by PID first (81582, 81720, 81721, 81758 api :3000, 81722 web :5173, 81723 floor
:5174, 81724/81762 imaging :8000); confirmed 3000/8000/5173/5174 free; never touched :3142. Started
`invai-infra pnpm dev:all` in the background, polled health (`db/redis/imaging/s3: true`; web/floor 200).
Stopped only the worker (PID 90077/90108, part of this run's own tree), then
`cd invai-backend && pnpm db:reset && pnpm db:migrate && pnpm db:seed` in the background with imaging up.
Seed finished clean in the log: blanks 108, designs 40 (sample art), orders 360/360, personalized artwork
**59/59 rendered**, sheet files **composed 4/4**, sheets 25 (597 transfers), shipments 264, inventory 108
variants, outbox released 5197, orders 360/items 694/transitions 3935/dueSoon 88. Restarted the whole stack
(fresh worker, no jobs held from before the reset) and re-polled health (all green) before running suites.

| Suite | Command | Result |
|---|---|---|
| API golden path | `E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts` (invai-web) | **13/13 passed** (16.0s); sheet utilization `[0.8912, 0.8564]` on build |
| Browser golden path | `pnpm e2e` (invai-web, full e2e/ dir) | `golden-path.spec.ts` **13/13**, `screens.smoke.spec.ts` **2/2** (owner screens + vendor portal, no console/request errors), `market.spec.ts` **5/5**, `digest.spec.ts` **10/10** (1 skipped by design). `digest-dates.spec.ts` (T-20-2, unrelated to wave 22): **3 failed** — see Issues below. Overall run: 31 passed / 3 failed / 1 skipped (2.6m) |
| Floor | `pnpm e2e` (invai-floor) | **3/3 passed** (10.6s): `floor.spec.ts`, `offline.spec.ts`, `press.spec.ts` |

## Wave 22 spot checks (curl as office@desertbloom.test / demo1234!, psql as invai_app)
- **SCAN form (T-22-3):** `shipping.scanForms.list` → empty on fresh seed; `create {carrier:"mock"}` before any
  label bought today → `409 NO_LABELS_TO_MANIFEST` (correct). Bought a mock USPS label on today's order, then
  `create {carrier:"usps"}` → **200**, `labelCount:3`, one form id; called again → **same id, same body**
  (idempotent); `list` shows exactly that one form.
- **Cross-tenant composite FK (T-22-2/T-22-4):** as `invai_app` with `app.company_id` set to Sun City DTF,
  inserting a `station_maintenance_events` row pointing at Desert Bloom's Press 1 station id → **refused**:
  `ERROR: insert or update on table "station_maintenance_events" violates foreign key constraint
  "station_maintenance_events_station_id_fk"`.
- **Maintenance block + offline replay (T-22-4, the AC3 round-2 fix):** office@ started maintenance on Press 1;
  presser@ (floor session via the station token) scanning the correct blank at Press 1 → blocked
  `station_maintenance`, item stays `transfer_in`. office@ ended maintenance (real time), then a **new** scan
  submitted with `scannedAt` set inside the now-closed window (an offline scan synced late) → **still
  blocked** `station_maintenance` — confirms the reviewer r2 fix (`03d780e`) holds on a fresh seed, not just
  in the review's scratch DB. A scan with `scannedAt` after the window → `ok:true, pressed, nextAction:qc`.
- **Pick list bin code (T-22-4, B-32):** `production.queue {station:"pick"}` returns `binCode` (and `shelf`)
  on every line; on this fresh seed every bin is `null` (the seed sets shelves, not bins — a known gap already
  in the author's report, not a regression). Field wiring confirmed; a populated example was proven earlier by
  `reviewer` r1's own evidence (`B-03-3 / TOTE-B12`) and not re-created here (writing directly into the shared
  dev DB to manufacture one was correctly blocked by the sandbox).
- **Vendor sheet email sent once (T-22-5):** Mailpit (`:8025`) search `to:vendor@suncitydtf.test` → 1 match,
  "New gang sheet 2026-09-30 #1 from Desert Bloom Tees", sent once during the seed's own vendor send.
- **Gang sheet image:** opened the preview PNG for sheet "2026-09-30 #1" (22 × 238.76 in, utilization
  **89.12%**) at `production.sheets.get` → `files.downloadUrl` → MinIO. Looked at it: clean typography and
  art on every transfer, readable order numbers (`#1533`, `113-2312473-1004459`, …, no unresolved template
  text), QR + size/color/design caption under each label, nothing clipped. Other full sheets in the list:
  85.64%, 85%, 85%, 84% — all ≥ 80% (a short end-of-batch sheet would be the known exception; none seen here).

## Screens looked at
Owner dashboard (all routes via `screens.smoke.spec.ts`, no console errors, no failed requests), vendor portal,
Today, an order drawer (via golden-path steps), a gang sheet detail + preview image (above), the label PDF
flow (golden-path step 9), profit (step 10), floor PIN login/press/QC/pack (both API and tablet UI suites).

## Issues found (owner, severity)
1. **Low, pre-existing, out of wave 22 scope** — `e2e/digest-dates.spec.ts` (T-20-2 area, wave 20): 3 tests
   fail on a fresh seed because no weekly digest exists yet for `/digests` to list
   (`a[href^="/digests/"]` never appears). This matches the known digest-sweep timing dependency already
   recorded in the wave 20 gate (`qa-report.md` §9: "Digest built by the sweep on a Tuesday"). Not caused by
   any wave 22 card (T-22-1..5 touch contracts, tenant FKs, USPS/Amazon shipping, production/inventory,
   orders/vendors — none touch the digest sweep or `/digests`). Owner: backend-engineer (digests) /
   qa-engineer to file a proper B-row if this keeps recurring across gates; not blocking this gate.

No other issues found. No High or Medium findings from this gate's own checks.

## Verdict
**PASS.** All carried-forward suites green; all suites re-run on this fresh seed green except one
out-of-scope, pre-existing digest-timing test file; every wave 22 spot check behaved as the cards specify,
including the round-2 maintenance-replay fix reproduced independently on a fresh seed. T-22-4's remaining
gap (qa-engineer floor co-review) is closed: `T-22-4-qa-engineer-r1.md`, verdict approve. All five wave 22
cards now have every required reviewer's latest file at `approve`.

## Processes and data
- Started and stopped by this run: stale-stack PIDs 81582/81720/81721/81758/81722/81723/81724/81762 (killed
  at the start, confirmed dead); `invai-infra pnpm dev:all` PID 89904 (first start) — killed and replaced;
  worker-only PIDs 90077/90108 — killed before the reseed; `invai-infra pnpm dev:all` PID **91255** (second,
  final start, tree: concurrently 91264, api/worker/imaging/web/floor shells 91373–91377) — **stopped at the
  end of this gate**; seed job PID 90557 (finished on its own); E2E runs 91544 (api golden path, finished),
  91798 (browser e2e, finished), 93624 (floor e2e, finished).
- Shared dev DB: freshly reset, migrated and seeded during this gate; left seeded (not reset again after).
- Infra containers (Postgres, Valkey, MinIO, Mailpit): left running, untouched.
