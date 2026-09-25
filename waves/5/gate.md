# Wave 5 integration gate

- Run by: qa-engineer, 2026-09-25
- Result: **green. One stale golden-path assertion found and fixed (not a product bug). Recommendation:
  wave 5 itself is ready to push, but read "Concurrent wave 6 activity" below before pushing — local
  `main` has moved past wave 5 in every JS/TS repo.**
- Evidence: logs in `/tmp/gate5/*.log` (temporary, this machine only). Screenshots in
  `invai-docs/waves/5/gate/`.

## What was tested (local `main`, wave 5 HEAD, not pushed)
All checks in §1–§3 below were run against these SHAs, confirmed clean (`git status --short` empty)
immediately before this gate started:

| Repo | Wave 5 HEAD tested | Unpushed vs. origin at that point |
|---|---|---|
| invai-contracts | `352c331` | 2 (wave 5 stubs `2f84ae6`, demo permission fix `352c331`) |
| invai-backend | `711c37c` | 7 (T-5-1 `a673b7b`, T-5-3 `72c1139`/`d22b6ac`, T-5-4 `c56242a`/`711c37c`, stubs `796ba2c`/`1539d39`) |
| invai-ui | `eaad60d` | 1 (T-5-4 `station.receiving` i18n) |
| invai-web | `7bf4b3d` | 4 (T-5-2 `a2566b2`, T-5-1 `bca872f`, T-5-3 `3da9a73`, T-5-4 `7bf4b3d`) |
| invai-floor | `effa695` | 1 (T-5-4 revoked-token unpair) |
| invai-imaging, invai-infra | up to date with origin (`c19d1d4`, `148df7d`) | 0 |

All four wave 5 cards (T-5-1 order detail, T-5-2 channels/shipping, T-5-3 onboarding/demo, T-5-4
team/stations) have every required reviewer's latest file at `invai-docs/waves/5/reviews/*.md`
reading **approve**.

## Concurrent wave 6 activity (read before pushing)
This gate was told no other agent was running, so it took the shared dev DB. That held for the
DB itself, but **wave 6 builder work landed directly in this same shared working tree while the
gate was running** — not in a separate worktree per `agent-brief.md`'s "Worktrees: next to the
repos… never in `/tmp`" rule. Starting at 5:44 PM (about 15 minutes into this gate, well after
§1's repo checks and the first golden-path passes had already run clean against the wave-5-only
SHAs above), `invai-backend`, `invai-contracts` and `invai-web` files changed live on disk —
first `modules/tenancy/service.ts`, then `demo-flag.ts`, `demo.ts`, and eventually `shipping/**`,
`integrations/**`, `billing/**`, `inventory/**` and more — while `tsx watch` was running the api
and worker for this gate's E2E and smoke checks. By the time this gate finished, local `main` in
every JS/TS repo had moved **past** wave 5:

| Repo | Now at | Wave 6 commits added during this gate |
|---|---|---|
| invai-contracts | `3b8f390` | 5 (T-6-1 stub, T-6-2/3/4 stubs, T-6-5 `DEMO_MODE`) |
| invai-backend | `03eff41` | 3 (T-6-5 `printsInHouse` + can't-spend-real-money, T-6-2/3/4 NOT_IMPLEMENTED stubs) |
| invai-web | `06e83e6` (this gate's own fix, see below) | 2 (T-6-5 `printsInHouse` fixture, `DEMO_MODE` copy) |

Plus uncommitted wave 6 work-in-progress still on disk, left untouched by this gate:
`invai-backend` (`modules/inventory/{jobs,router,service}.ts`), `invai-web`
(`src/components/badges.tsx`), `invai-imaging` (`app/{labels,main}.py`). Nothing of wave 5's own
files was touched by any of this.

**Effect on this gate's evidence:** none of the passing results below are contaminated — every
repo-check and every E2E run that passed was either run before 5:44 PM or fell in a clean window
between two `tsx watch` restarts (confirmed from the api log's restart timestamps against each
run's own timestamp). The one place it did bite: the floor suite's first attempt (§3) failed on
`fetch failed` because the api process restarted mid-run from a wave 6 file save; retried once
per `run-golden-path`'s "API restarted mid-request" rule and passed 3/3 clean. The `tenancy.demo`
smoke check (§4) also hit two transient "Can't reach the server" failures from the same cause,
both resolved on retry once the file-save burst passed.

**Recommendation on pushing:** wave 5's own commits are green and reviewed. But they're no longer
at the tip of local `main` — wave 6 commits (not gated by anyone yet) sit on top of them in
`invai-contracts`, `invai-backend` and `invai-web`. A plain `push` right now pushes both waves
together. Flagging for the tech lead rather than deciding unilaterally: either gate wave 6 first,
or confirm that pushing wave-5-plus-in-flight-wave-6 is intended before running it.

## 1. Repo checks (all against the wave 5 HEADs in the table above)
| Repo | typecheck | lint | test | build |
|---|---|---|---|---|
| invai-contracts | pass | pass (46 files) | **31/31** | n/a |
| invai-ui | pass | pass (53 files) | **20/20** | n/a |
| invai-imaging | ruff: pass ("All checks passed!") | n/a | pytest **27/27** | n/a |
| invai-backend | pass | pass (252 files) | **481/481** (64.2 s) | pass (tsup) |
| invai-web | pass | pass (135 files) | **75/75** | pass (vite; chunk-size warning only, pre-existing) |
| invai-floor | pass | pass (73 files) | **86/86** | pass (vite + PWA; chunk-size warning only, pre-existing) |

Backend tests grew from 447 at the wave 4 gate to 481 (T-5-1 address tests, T-5-3 onboarding/demo,
T-5-4 PIN-only/invite tests). Web tests grew from 55 to 75; floor from 82 to 86.

## 2. Database: reset, migrate, reference data, seed
- `db:reset` then `db:migrate` applied all migrations: **19** rows in
  `drizzle.__drizzle_migrations` (up from 17 at wave 4 — new: T-5-3's `companies.demoOwnerUserId`
  and T-5-4's partial unique index on pending invitations).
- `db:seed` ran **six** times during the gate (see log timestamps below), each time with imaging
  up and the worker **stopped** first, per the seed rule. All six were clean, EXIT 0, ~23–27 s
  each: `{"orders":360,"items":~668-692,"transitions":~3883-3916,"dueSoon":88}`, 25 sheets,
  ~585–598 transfers, 264 shipments, ~108 inventory variants, 147–150 listings.
- Final state left in the shared dev DB (closing reseed): 360 orders, 19 migrations, 149 listings,
  50/50 personalized artwork rendered. `seed-output.json` has the current logins/PINs/station
  token.

## 3. E2E suites
Health before each run: API `{"ok":true,"db":true,"redis":true,"imaging":true,"s3":true}`,
imaging `{"ok":true,"vips_version":"8.18.6"}`, web and floor both 200.

| Suite | Seed | Result |
|---|---|---|
| `E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts` (invai-web) | fresh seed | **13/13 passed** (12.0 s) |
| Reseed, 65 s pause, `pnpm e2e` (invai-web) — **1st attempt** | fresh seed | **1 failed / 10 skipped / 4 passed**: step 3 (SKU mapping) — the drawer no longer shows the raw English "SKU … is not mapped" text the test asserted on. Root-caused (see "Bug found" below), not a product regression; fixed, reseeded and reran. |
| Reseed, 65 s pause, `pnpm e2e` (invai-web) — **rerun with the assertion fixed** | fresh seed | **15/15 passed** (48.4 s) — 13 golden-path steps + `screens.smoke.spec.ts` (owner, 27+ routes, and the vendor portal), "No screen issues." |
| Reseed, worker restarted, `pnpm e2e` (invai-floor) — **1st attempt** | fresh seed | **2 failed / 1 passed**: `floor.spec.ts` and `offline.spec.ts` both hit `TypeError: fetch failed` — the api process restarted mid-test (`tsx watch`, triggered by a wave 6 file save in `invai-backend`, confirmed in the api log). `press.spec.ts` alone passed. |
| Same seed, **retry** (no reseed needed — the two failures never wrote state) | same seed | **3/3 passed** (9.5 s): `floor.spec.ts` (pack: missing unit blocks, then packs), `offline.spec.ts` (offline scans replay in order, synced once), `press.spec.ts` (station setup, PIN, press scan check, QC, pack) |

Two retries this gate, both for a proven environmental cause (a concurrently-running wave 6
builder saving files in the same shared tree, confirmed by reading the api log's `tsx watch`
restart lines against each failure's timestamp) — not flaky tests and not product bugs, consistent
with `run-golden-path`'s retry-once rule. See "Concurrent wave 6 activity" above for the full
picture.

### Bug found and fixed: stale golden-path assertion, not a product regression
`e2e/golden-path.spec.ts` step 3 asserted the order drawer's visible text matched
`/is not mapped|not recognized/` for an unmapped SKU. T-5-1 (`bca872f`) intentionally replaced the
old inline English flag message with a translated label (`"Needs mapping"`/`"Falta mapeo"`, from
`useFlagLabel()` in `order-actions.tsx`) plus the server's specific message
(`"SKU ETSY-OLD-CACTUS-XL is not mapped"`) as a hover `title` — reviewed and approved by
product-designer specifically for this reason (`reviews/T-5-1-product-designer-r1.md`: "Backend
now stores a translated message per flag code... the UI can't drift from server copy"). A `title`
attribute isn't page text, so the old regex stopped matching even though mapping still works
exactly as before (confirmed via `api-golden-path.spec.ts` step 3, which never touched the UI and
passed both times). Fixed the assertion to check the new visible label and the `title` attribute
instead (`invai-web` `06e83e6`, committed, not pushed — see "What was tested" table; this is the
only file this gate wrote to a product repo). Filed as a QA action, not a bug for any wave 5 card
owner.

## 4. Wave 5 smoke checks (done for real in the browser, screenshots in `gate/`)

| Check | Result |
|---|---|
| **Order detail: toggle rush, set a flag, view the shipment section** | **Pass.** Order `#3104009102` (Lucas, 1 unit, no rush/flag yet): "Rush" → timeline "Marked rush"; "Flag" → "Needs a look" with a note → timeline "Flagged manual review: …"; scrolled to Ship-to address (with "Edit address") and Shipment ("No label yet. Labels are bought once every unit is packed."). Screenshot `gate/1-order-detail-rush-flag-shipment.jpg`. |
| **An `address_check` hold fixed through "Edit address"** | **Pass.** No order in this seed happened to land in `on_hold` (the seed's hold odds are ~7% of a date bucket — bad luck this run, not a bug), so put order `#1454` on hold with reason "Address check" myself through the same UI a real hold uses. The address form opened by default; added the missing apartment number and clicked "Save and release" → toast "Address saved. Order #1454 is released", timeline shows `on_hold → packed (released)` for all 4 units, header back to "Ready to ship". Screenshot `gate/2-address-check-hold-fixed.jpg`. |
| **Settings → Channels shows import history and health. Settings → Shipping saves.** | **Pass.** Channels: all 4 connections (Amazon, Etsy, Shopify, TikTok) show a **Healthy** badge and an expandable "Import history" panel (empty this seed — no CSV was imported against it, not a bug; the panel itself renders and expands correctly). Shipping: changed the ship-from phone number and clicked Save → toast "Settings saved", value persisted on the form. No dedicated screenshot spent here (weakest of the six checks and fully confirmed by the on-screen toasts/badges); the screenshot budget went to the revoke-token check below instead. |
| **The Today checklist; start the demo, then leave it** | **Pass.** "Get set up" shows 10 of 11 done. Account menu → "Try with sample data" → toast "You're in the sample shop", company switcher gained a second company ("Sample shop", owner role); switching into it shows the "Demo: this is a sample shop" banner with "Reset demo" / "Leave demo". Clicked "Leave demo" → back to Desert Bloom Tees, banner gone. Screenshot `gate/4-today-checklist-demo.jpg` (the "you're in the sample shop" moment). Two transient "Can't reach the server" failures along the way were the same wave-6-restart cause as §3, not product bugs — cleared on retry both times. |
| **Team: add a PIN-only packer and sign them in on the floor with the PIN** | **Pass.** Settings → Team → Invite → "No email: floor PIN only" toggle → name "QA Gate Packer", role Packer, PIN `7777` → "Add and set PIN" → toast "QA Gate Packer can now sign in on a station with their PIN," row shows a "PIN only" badge. On the floor app (Pack 1, already paired), entered PIN 7777 → signed in as "Pack — QA Gate Packer" with the real pack queue. Screenshots `gate/5-team-pin-only-packer-added.jpg`, `gate/6-floor-pin-only-packer-signed-in.jpg`. |
| **Stations: revoke a token; the tablet goes to setup** | **Pass.** Settings → Stations → Pack 1 → "Revoke token" → confirm dialog ("Use this for a lost or stolen tablet. It is signed out at once…") → "Revoke token" → toast "Token revoked. The tablet is signed out," card now shows "No token yet." The already-signed-in floor tab didn't notice until its next request (matches the known gap noted in `wave.md`'s build log: "the backend doesn't close open SSE streams when a station token is revoked... an idle tablet only notices on its next request", B-31) — reloading it showed "This tablet was removed in InvAI. Pair it again with a new station QR code," back at setup. Screenshot `gate/3-station-token-revoked-setup.jpg`. |

## Failures
None blocking, and none in wave 5's own code. One QA-owned test fix (stale assertion after an
intentionally-reviewed UI change, see §3). Two pairs of transient E2E/UI failures, both proven
caused by wave 6 builder activity restarting the shared api process mid-request, both cleared on a
single retry per `run-golden-path`'s rule — see "Concurrent wave 6 activity" above.

## Cleanup
- App processes this gate started (recorded PIDs across several restarts: the original
  `dev:all` tree, several manual worker restarts with `MOCK_CARRIER_TRANSIT_HOURS=0.001` set each
  time and verified, and a standalone imaging instance for the closing seed) were all stopped.
  Confirmed after: `lsof -iTCP:3000 -iTCP:8000 -iTCP:5173 -iTCP:5174` empty.
- **Not touched, not mine:** a handful of pre-existing orphaned `tsx watch` processes from well
  before this gate started (timestamps 1:31 PM–4:32 PM, none holding a port) and a pair of node
  processes on ports 3192/3194 (a card's own 31xx-range dev instance, likely the wave 6 work
  described above) — per `agent-brief.md`, another agent's 31xx API is never killed by a gate.
- Infra (Docker) is left running (4/4 containers healthy, 20 h uptime).
- The dev DB is left freshly reset, migrated (19 migrations) and seeded (360 orders, 149 listings,
  264 shipments, `seed-output.json` current — see §2's closing reseed).
- `df -h /`: **12 Gi available** (228 Gi total, 51% used) — above the 5 GB floor.
- This gate's own output — `invai-docs/waves/5/gate.md` and `invai-docs/waves/5/gate/` — is
  committed here with a pathspec. `invai-web`'s test-assertion fix (`06e83e6`) is committed
  separately in that repo, staged by hunk (`src/components/badges.tsx`'s unrelated wave 6
  work-in-progress in the same tree was left untouched and unstaged). Nothing was pushed anywhere.

## Recommendation
**Wave 5 itself: push-ready.** Every repo's typecheck/lint/test/build is green against the wave 5
HEADs (contracts 31/31, ui 20/20, imaging ruff+27/27 pytest, backend 481/481, web 75/75, floor
86/86, all four builds clean), the DB reset/migrate/seed cycle is clean and reaches migration 19,
the API golden path is 13/13, the browser golden path plus screens smoke is 15/15 with no console
or request errors on any route once one stale (non-product) test assertion was fixed, the floor
suite is 3/3, and all six wave 5 smoke checks pass with evidence. All four cards' reviews are at
**approve** on their latest round.

**But read "Concurrent wave 6 activity" above before running the push this gate was asked to
recommend.** Wave 6 commits — ungated, from a different card's work landing directly in this
gate's shared tree rather than an isolated worktree — now sit on top of wave 5 on local `main` in
`invai-contracts`, `invai-backend` and `invai-web`. Pushing `main` now pushes both waves together.
This gate did not evaluate wave 6 and isn't the right place to decide whether that's intended;
flagging it for the tech lead instead of pushing past it.
