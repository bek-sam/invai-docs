# Wave 1 integration gate

- Run by: qa-engineer, 2026-09-24 (about 15:40–16:10 local)
- Result: **all green. Recommendation: push** (see "Recommendation" for one thing to check first).
- Evidence: logs in `/tmp/gate1/*.log` (temporary). Screenshots in `invai-docs/waves/1/gate/`.

## What was tested (local `main`, not pushed)
| Repo | HEAD | Unpushed commits |
|---|---|---|
| invai-backend | `d97cd3c` | 10 (T-1-1 `34ed022` `293047b`, T-1-2 `90657ac`, T-1-3 `b117997` `ed8a300`, T-1-4 `55ca092` `659f1bc`, T-1-5 `8becdb5` `b8d0471`, plus **wave 2 stub** `d97cd3c` billing checkout/portal NOT_IMPLEMENTED) |
| invai-contracts | `a3b4067` | 2 (T-1-3 stub `1a22b29`, plus **wave 2 stubs** `a3b4067`) |
| invai-web | `dc9f655` | 2 (T-1-4 `d6336e0`, plus `dc9f655` PO badge "submitting") |
| floor, imaging, ui, infra | up to date with origin | 0 |

All working trees were clean before and after the run.

## Clean start
- Infra: `local-postgres-1`, `local-valkey-1`, `local-minio-1`, `local-mailpit-1` were all healthy.
- Ports 3000–3199, 5173, 5174 and 8000 were free.
- One stale process: an orphaned `pnpm dev:api` / `tsx watch src/api/server.ts` from `/private/tmp/r14/invai-backend` (PIDs 686 and 704, parent PID 1, not listening on any port). I stopped it, as the gate brief asked.
- Node v24.21.0.

## 1. Repo checks
| Repo | typecheck | lint | test | build |
|---|---|---|---|---|
| invai-contracts | pass | pass (46 files) | **31/31** (4 files) | n/a |
| invai-ui | pass | pass (53 files) | **20/20** (4 files) | n/a |
| invai-backend | pass | pass (198 files) | **231/231** (39 files) | pass (tsup) |
| invai-web | pass | pass (97 files) | **23/23** (5 files) | pass (vite; chunk-size warning only) |
| invai-floor | pass | pass (57 files) | **41/41** (5 files) | pass (vite; chunk-size warning only) |
| invai-imaging | ruff: pass ("All checks passed!") | n/a | pytest **27/27** | n/a |

Backend tests grew from 148 at v1 hand-off to 231.

## 2. Database: reset, migrate, reference data, seed
- `db:reset` then `db:migrate` applied all 9 migrations: `drizzle.__drizzle_migrations` has 9 rows (0000–0008), and `public` has 63 tables including `webhook_deliveries`.
  - Migrate prints `[migrate] up to date (invai)` even on a freshly reset DB. The message is misleading but harmless (cosmetic; backend-foundation).
- Reference data: `trademark_marks` = **471** (the gate needs > 400), and `plans` = **5**.
- `db:seed` ran with imaging up and the worker stopped. EXIT 0, 24 s: `{"orders":360,"items":681,"transitions":3894,"dueSoon":88}`, 25 sheets and 595 transfers, 48 personalized artworks rendered.
- The browser suite got its own fresh reset, migrate and seed (worker stopped, then API and worker restarted). The DB was reset, migrated and seeded again at the end.

## 3. E2E suites
Health before the run:
- API: `{"ok":true,"db":true,"redis":true,"imaging":true,"s3":true,"version":"0.1.0"}`
- Imaging: `{"ok":true,"vips_version":"8.18.6"}`
- Web and floor: both 200.

| Suite | Seed | Result |
|---|---|---|
| `E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts` (invai-web) | fresh seed 1 | **13/13 passed** (8.2 s). Sheet utilization 0.8792 and 0.9055 |
| 70 s pause for the sign-in limit, then `pnpm e2e` (invai-web) | fresh seed 2 | **15/15 passed** (43.8 s): golden path 13/13 and screens smoke 2/2 (every owner route, plus the vendor portal) |
| `pnpm e2e` (invai-floor) | seed 2 | **1/1 passed** (2.9 s): pair, PIN, wrong blank BLOCKED, right blank PRESS, QC, pack |

Browser step 6 (vendor, the known flaky `clickIfShown`) passed on the first try (2.3 s), so it was not re-run.

## 4. Wave 1 smoke checks (done for real)
| Check | Card | Result |
|---|---|---|
| Owner invites a teammate from Settings > Team (role Presser) | T-1-4 | **Pass.** Toast "Invitation sent to gate.w1.…@example.test" (`gate/1-owner-invite-sent.png`) |
| The email arrives in Mailpit | T-1-4 | **Pass.** Subject "Riley Owner invited you to Desert Bloom Tees on InvAI". The body says "…as Presser", with an "Accept invitation" button and "works until October 1" (`gate/2-mailpit-email.png`). The link is `http://localhost:5173/accept-invite/<uuid>` |
| Accept in a fresh browser and land with the right role | T-1-4 | **Pass.** The accept page reads "Desert Bloom Tees invited you to join as Presser", with the email locked (`gate/3-accept-page.png`). After sign-up the user lands on `/`: Today, "Good afternoon, Gate", with the presser menu (Today, Orders, Gang sheets, Stations board, Company) (`gate/4-landed.png`). In the DB, the member is `presser / active` and the invitation is `accepted` |
| Unsigned `POST /webhooks/shopify` | T-1-2 | **Pass.** `401 {"error":"invalid signature"}`. A bad `x-shopify-hmac-sha256` also returns 401. `webhook_deliveries` has 0 rows, so nothing was stored before verification |
| `/health` has no `mocks` field | T-1-1 | **Pass.** The keys are `ok, db, redis, imaging, s3, version` |
| Production env guard | T-1-1 | Not exercised (development only, as briefed). Development starts normally on mocks |
| Reference data on a fresh DB | T-1-5 | **Pass.** 471 marks and 5 plans straight after `db:migrate`, before the seed. The golden-path step 11 trademark check flagged Nike |

## Failures
None. No test was retried, skipped or loosened.

Minor observations (not blocking):
- `[migrate] up to date` is printed after applying 9 migrations to an empty DB (backend-foundation, cosmetic).
- The web and floor builds warn about chunk size (known, pre-existing).

## Cleanup
- I stopped every process I started: imaging 7316, api 7435 and its restart, worker 7436 and its restart 7649, web 7437 and floor 7438, including their child processes.
- Afterwards, nothing listens on 3000–3199, 5173, 5174 or 8000, and no tsx, uvicorn or vite processes remain.
- Infra (Docker) is left running.
- The dev DB is left freshly reset, migrated and seeded (seed 3: 360 orders, 471 marks, 5 plans, no gate test users). `seed-output.json` has the new station token.
- I didn't edit any code, and I didn't push anything.

## Recommendation
**Push.** Wave 1 passes every check on a fresh seed.

Before pushing, the tech lead should confirm that the three wave 2 stub commits are meant to go in the same push. They are backend `d97cd3c`, contracts `a3b4067` and web `dc9f655`, and they sit on top of the wave 1 commits. This gate tested them together with wave 1, and they broke nothing. But no wave 1 review covers them. If they need their own review first, push only up to backend `659f1bc`, contracts `1a22b29` and web `d6336e0`. Those states were not gated on their own, so re-run this gate in that case.
