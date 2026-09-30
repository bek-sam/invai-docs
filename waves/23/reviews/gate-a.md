# Wave 23 integration gate — part A (T-23-0, T-23-7)

SHAs (unpushed, local HEADs): backend d39a481, contracts 7ee15b6, ui 952c174, web 54b64d7,
floor a902ec3, imaging 58b67ee, infra 490884d.

## 1. Backend full suite (d39a481)
- `pnpm typecheck && pnpm lint`: clean (`tsc --noEmit` OK; biome "Checked 420 files... No fixes applied.").
- `pnpm test`: first run in this session hit the documented collision — `src/modules/market/service.test.ts`
  failed at suite level (`afterAll` hook timed out, 60000ms) while another background run touched
  `invai_test` concurrently. A full retry (no other DB users) passed clean:
  `Test Files 156 passed | 2 skipped (158)`, `Tests 1205 passed | 3 skipped | 1 todo (1209)`, exit 0.
  No re-run of the single file was needed since the full retry already went green.
- **Verdict: PASS.**

## 2–8. Golden path on a fresh seed
Stack started (`invai-infra pnpm dev:all`), `pnpm db:reset && pnpm db:migrate && pnpm db:seed`
(imaging up throughout), apps restarted once, health checks all OK (api/imaging/web/floor).

- `E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts`: **13/13 passed** (12.8s). Sheet utilization
  in-run: 0.8603 / 0.8942 (both ≥ 80%).
- `pnpm e2e` (invai-web, golden-path + screens.smoke + digest/market/digest-dates):
  first pass showed 9 failures. Root-caused two as missing gate preconditions documented in the
  spec files themselves and in `qa-report.md` §7/§8 (not product bugs):
  - `digest.spec.ts` (3 tests) and the public-unsubscribe skip needed `digest.build` forced for
    Desert Bloom Tees, week `2026-W39` (spec header: "Runs against the seeded stack after a
    digest has been built for the current week ... per wave.md's integration gate"). Forced it
    via a temporary, uncommitted script calling `buildDigest()`/`unsubscribeLink()` directly
    (deleted immediately after, `git status` clean in invai-backend), then re-ran with
    `E2E_DIGEST_UNSUB_TOKEN` set.
  - `market.spec.ts:91` (1 test) needed the market jobs run on the fresh seed — a known,
    previously-filed gap (`qa-report.md` wave-18 gate notes: "on a fresh seed with a worker
    running, `market.sweep` treats the day as done after the outbox-triggered `computeSignals`
    and never enqueues `refreshDemand`, so no outside mock sources, no `Sample data` badge...
    until 03:00 UTC" — filed to backend-engineer/market). Ran `refreshDemand()` +
    `computeSignalsForShop()` by hand via the same throwaway-script pattern, deleted after.
  - Re-run after both fixes: **34/35 passed**, 1 failed:
    `digest-dates.spec.ts:33 AC1 — the Spanish digest heading never shows an English
    weekday/month`. This is the documented **known failure B-207**. Not counted as new.
  - `screens.smoke.spec.ts`: all routes clean, "No screen issues", vendor portal renders clean.
- `pnpm e2e` (invai-floor): **3/3 passed** (9.1s) — pair/PIN/press/QC/pack, offline replay,
  server-rejected-scan park+alert.
- **B-208 (0.7951 sheet-efficiency race):** not observed this run (utilizations were 0.8603/0.8942
  throughout).

**Verdict: PASS** — all suites green except the one documented known failure (B-207).

## 9. Visual spot-check (screenshots taken via a throwaway Playwright script, not committed;
saved under my scratchpad, not in any repo)
- **Today (en/es):** real numbers, no `##` order numbers, "Get set up" checklist correct, digest
  card shows `$972.48 (-13.3%)`. Station work bars and alerts render.
- **Order drawer (en):** real order number `#113-2000000-1000000`, items, timeline, shipment,
  ship-to — all correct. No broken `<img>` tags anywhere (systemic — see bug below).
- **Gang sheet (en):** film use **89%** (≥ 80%), 10 real placements with real order numbers
  (`#1536`, `#3104011248`, `#113-2321583-1004589`, ...), no `##`.
- **Profit (en/es):** revenue/costs/fees/refunds/net/margin all sane and consistent between
  languages; es numbers use `13.939,30 US$` formatting.

### Issues found (not fixed — filed here for the tech lead to route)
1. **Medium — no design/order-item thumbnails anywhere (systemic).** Every design and order-item
   thumbnail shows the `image-off` placeholder icon (checkerboard bg), catalog-wide (40/40
   designs on `/catalog/designs` show the placeholder; `img` count on that page = 0). Root cause:
   `designs.list`'s placements always return `previewKey: null` (confirmed via the live
   `/rpc/designs/list` response) — `fileKey` (the source art) is set, but nothing in
   `invai-backend/src/modules/catalog/*` or `src/db/seed/builder.ts` ever populates
   `previewKey` for a design placement (only gang-sheet `previewKey` is set, in
   `src/db/seed/builder.ts`). This looks pre-existing, not caused by this reset. Owner:
   backend-foundation/catalog (whoever owns design preview generation) + web-engineer to confirm
   the frontend's fallback is intended when `previewKey` is null vs. always expected to be set.
2. **Low — Spanish Today-page date/alert-body text not translated.** `invai.lang=es`: the
   greeting still reads `"Buenas noches, Riley. Tuesday, September 29"` (English weekday/month,
   same class of bug as B-207 but a different component — the Today greeting subheading, not the
   digest heading) and an alert body reads `"Pedido con fecha de envío vencida" / "Order
   3310000003 is past its ship-by"` (title translated, body text not). Owner: web-engineer
   (Today screen date formatting + alerts feed i18n).

## Processes and data
- Started and stopped (recorded PIDs): backend typecheck/lint bg (45065, done before stop
  needed), `invai-infra pnpm dev:all` run 1 (45202/45211, stopped for the restart), run 2
  (46313/46323, stopped at cleanup). Confirmed ports 3000/5173/5174/8000 free after stop.
- Did not touch: API :3142 (PID 98947, tsx watch 11838), vite :5183 (73962), tail -f (10572).
- Scratch backend scripts (`__qa-force-digest.ts`, `__qa-force-market.ts`, `__qa-shots.mjs` and
  helpers) were created outside owned paths only as throwaway verification tools, run, and
  deleted; `git status --short` is clean in invai-backend and invai-web.
- Shared dev DB (`invai`): freshly reset, migrated and seeded this run; digest built for
  2026-W39 and market signals computed for Desert Bloom Tees as part of verification (both are
  additive/idempotent, not schema or code changes). Infra containers left running.
- `invai_test`: 1 idle connection at final check (my own psql query), no other activity.

## Overall: PASS
Backend suite green, full golden path green (API 13/13, browser 34/35 with only the known
B-207, floor 3/3), screens clean, two real product issues found and filed above (not fixed by
QA per role).
