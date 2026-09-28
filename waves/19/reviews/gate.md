# Wave 19 integration gate

Reviewer: qa-engineer, on Fable 5.1. Ran 2026-09-28 08:52–09:20 (machine clock, America/Chicago; the seed shop is America/Phoenix, two hours behind).

Commits under test (local, not pushed):
- invai-contracts `83eee25` (0.7.0)
- invai-backend `53cc86a`
- invai-web `1e4d307`
- invai-floor `68b9cbb` (no wave-19 commits; contract consumer)

Cards T-19-1..5, all approved (reviews in `invai-docs/waves/19/reviews/T-19-*`).

## Verdict

**PASS.** Every repo check is green; on one fresh seed the API golden path is 13/13, the floor suite 3/3, and the full browser run (`pnpm e2e`: digest, golden path, market, screens smoke) is 27/28 in one go with **no 429s** (B-133 fixed). The one red result was my own selector in `e2e/digest.spec.ts` (it counted feedback and vote buttons as actions; the page renders exactly 3 action links); fixed in QA's file and re-run 8/8 (uncommitted, issue 7 below). The digest for the seed shop was built by the worker's own hourly sweep at exactly 07:05 Phoenix, its numbers equal the profit page for that week, one email reached Mailpit with the RFC 8058 headers and the placeholder postal address, one-click unsubscribe is idempotent, plan usage shows only to `billing.read`, presser is `FORBIDDEN`, and no AI summary text appears anywhere (`narrativeStatus: shadow` only). Both scale budgets hold with a wide margin. Recommendation: push, with issues 1–3 as cards.

## 1. Pre-checks — PASS

- `@invai/contracts` links: backend, web and floor all `-> ../../../invai-contracts`.
- `df -h /`: 228Gi total, **11Gi available**.
- Infra: `local-postgres-1`, `local-valkey-1`, `local-minio-1`, `local-mailpit-1` all `Up (healthy)`.
- Processes before start (not mine, left alone): `tsx watch src/api/server.ts` chains on `:3000` (pid 40324, parent since Sep 26 12:46), `:3142` (pid 40321, parent since Sep 26 23:24) and `:3178` (pid 40322, parent since Sep 27 22:25, health `db:false`, a reviewer's port pointing at a dropped DB). `:3000` health `ok` and serves the current code (`digest.latest` and `me.notifications.get` answer signed in as owner), so the gate used it. No worker, imaging, web or floor running. All four code repos clean.

## 2. Repo checks — PASS (all four repos)

| Repo | Command | Result |
|---|---|---|
| invai-contracts | `pnpm typecheck && pnpm lint && pnpm test` | tsc clean; biome 55 files clean; **7 files / 68 tests passed** |
| invai-backend | `pnpm typecheck && pnpm lint && pnpm test` | tsc clean; biome 382 files clean; **130 files passed, 1 skipped / 1068 tests passed, 2 skipped, 1 todo** (255.5 s, on `invai_test`) |
| invai-web | `pnpm typecheck && pnpm lint && pnpm test && VITE_API_URL=http://localhost:3000 pnpm build` | tsc clean; biome 166 files clean; **17 files / 97 tests passed**; build `✓ built in 1.52s` |
| invai-floor | same as web | tsc clean; biome 76 files clean; **9 files / 96 tests passed**; build ok (`precache 15 entries`) |

## 3. Fresh seed — PASS

Started imaging (`uv run uvicorn app.main:app --port 8000`, pid 46343), web (pid 46344, `:5173`) and floor (pid 46345, `:5174`); health `{"ok":true,"vips_version":"8.18.6"}`, web 200, floor 200. With imaging up and no worker: `pnpm db:reset && pnpm db:migrate && pnpm db:seed` → `[migrate] up to date (invai)`, `[seed] done {"orders":360,"items":679,"transitions":3907,"dueSoon":88,"seconds":23}` at 08:59 (`seed-output.json` written by the seed). API health after: `{"ok":true,"db":true,"redis":true,"imaging":true,"s3":true}`. Then owner@ opted in (`me.notifications.set {kind:"digest", on:true}` → `on:true, source:"settings"`, from `on:false, source:null` on the fresh seed), then the worker fresh: `MOCK_CARRIER_TRANSIT_HOURS=0.001 pnpm dev:worker` (pid 46555), 55 jobs registered including `digest.sweep/build/deliver/purge`.

Environmental noise, not a bug: the fresh worker replayed stale BullMQ jobs from before the reset (`ai.generateListingDrafts … listing draft … not found`, `final:false`); `db:reset` doesn't flush Valkey.

## 4. Golden path — API PASS, browser PASS (27/28, the red one is QA's selector), floor PASS

**API golden path** (`E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts`, run after the digest build so the digest week stayed untouched): **13/13 passed (12.1 s)**. Sheet utilization `[0.8341, 0.8314]`, lengths `[237.93, 57.05]`.

**Full browser run** (`E2E_DIGEST_UNSUB_TOKEN=<token from the email> pnpm e2e`): **27 passed, 1 failed (1.5 m)**, one attempt, no retries (`retries: 0`).
- digest.spec 7/8, golden-path 13/13, market 5/5, screens.smoke 2/2 ("No screen issues."). The market vote test and `/settings/billing` passed inside the full run: no `429` anywhere (wave 18 issue 1 / B-133 is fixed).
- The failure, `digest.spec.ts:54 English: glance block, up to 3 actions…`: `expect(received).toBeLessThanOrEqual(3)` received 10. The ARIA snapshot shows the page renders exactly 3 actions as links ("Ship 13 overdue orders", "Reorder Bella+Canvas BC3001 Black XL", "Reorder Gildan G64000 Navy S"); the test's `getByRole("button", { name: /Ship|Reconnect|Review|List|Reorder/i })` matched the 6 "Helpful: …" / "Not helpful: …" thumbs and the 4 Market watch "Mark 'List …'" vote buttons. Layer at fault: the test (QA). Fixed to count the action links (1–3) and to click a real "Not helpful:" button (the old `/thumbs up|👍/` guard never matched, so the feedback assertion had silently never run); re-run `playwright test e2e/digest.spec.ts` → **8/8 passed (7.9 s)**, including the feedback reason "Not relevant" and the unsubscribe page.
- Expected skip notes in golden-path stdout ("item already mapped on a previous run", "item is shipped; skipping the build", "order already shipped… checking the shipment only"): the API suite ran first on the same seed.

**Floor tablet suite** (`pnpm e2e` in `invai-floor`): **3/3 passed (9.1 s)**: pack blocks a missing unit, offline replay parks a rejected scan, station setup / PIN / press check / QC / pack.

## 5. Digest on the fresh seed — PASS

- **Built by the sweep, not forced.** The worker's `digest.sweep` scheduler (`5 * * * *`) fired at 14:05:00Z = 07:05 Phoenix on this Monday, found Desert Bloom past its default Mon 07:00 slot and built `2026-W39` (Sep 21–27): worker log `digest built {weekKey:"2026-W39", status:"ready"}`, `digest sweep {"built":1,"failed":0}`, then `digest.ready` → `digest.deliver` → `mail sent` + `user email sent` for owner@ in the same second (`digest.latest`: `readyAt 14:05:00.116Z`, `net $652.92`, `netChange -37.9%`, `actionCount 3`, `narrativeStatus "shadow"`).
- **Numbers equal the profit page.** `finance.profit {dimension:"channel", period: Sep 21 00:00 → Sep 28 00:00 Phoenix}` as owner: revenue 198336, net 66088, margin 33.32 %; the digest says 195637 / 65292 / 33.4 %. The difference is exactly golden-path order `3310000004` (placed Sep 23, revenue 2699, net 796), imported at 14:05:35Z, 35 s after the build: 198336 − 2699 = 195637 and 66088 − 796 = 65292. Orders 35 vs previous 73, on-time 100 %.
- **Email in Mailpit** (`GET /api/v1/message/2Od28hwv91ZEQKMvkP2x2N/headers`): `From: InvAI <sheets@invai.local>`, `To: owner@desertbloom.test`, `Subject: Your week at Desert Bloom Tees: net profit $652.92 (-37.9%)`, `Message-Id: <digest.<digestId>.<userId>@invai.local>`, **`List-Unsubscribe: <http://localhost:3000/l/<token>>, <mailto:sheets@invai.local?subject=unsubscribe%20digest>`**, **`List-Unsubscribe-Post: List-Unsubscribe=One-Click`**. Body: glance lines, 3 actions with `/l/` click links, Market watch (2 items, "Sample data, not your real market…"), footer "You get this because you turned on the weekly review for Desert Bloom Tees." + "Unsubscribe with one click: …" + "Manage in Settings" + **"InvAI, postal address pending (OI-12), USA"**. No `<img>` (no pixel), no "summary"/"resumen"/"upgrade"/"promo" text, 6 distinct `/l/` links. One digest email only (Mailpit search on the subject: 1 match).
- **One-click unsubscribe:** `POST /l/<token>` (form `List-Unsubscribe=One-Click`) twice → `{"ok":true}` 200 both times, `me.notifications.get` after each: `on:false, source:"unsubscribe_link", updatedAt 14:07:48.820Z` (same value → one change). `GET /l/<token>` → `302 → http://localhost:5173/unsubscribe?token=…`, preference unchanged. Tampered token → `302 → /unsubscribe?error=invalid`. Undo (`POST` JSON `{"undo":true}`) → `{"ok":true,"undone":true}`, `on:true, source:"settings"`; undo again → `409 {"error":"not_unsubscribed"}`. The browser suite then used the same token: the page posts once and shows the Undo message.
- **`digest.get {weekKey:"2026-W39"}`:** owner → full digest with `planUsage {ordersUsed:338, ordersLimit:10000, aiCreditsRemaining:1946}`; office → same digest **without** `planUsage` (key absent); presser → `FORBIDDEN` (`Missing permission finance.read for digest.get`).
- **Shadow mode:** the owner payload has `narrativeStatus: "shadow"` and no narrative/summary key; the email, the digest page (en/es), Today and Settings show no AI text; the AI toggle is disabled with "Turned off for now while we test AI summaries…" (e2e test 5).
- Not observed: the 08:05 Phoenix sweep (10:05 machine time) that should build 0 for Desert Bloom; the second-sweep no-duplicate property is covered by the AC29 run below (`built 0` on the second sweep) and by the module's tests.

## 6. Scale runs — PASS (both budgets)

Own database `invai_t19_qa_scale` (created and migrated by vitest's global setup through `TEST_DATABASE_URL`/`TEST_MIGRATION_DATABASE_URL`), dropped afterwards; Redis DB 15 flushed.

| Run | Fixture | Result | Budget |
|---|---|---|---|
| Digest AC29, single large shop (`DIGEST_SCALE=1 vitest run src/modules/digest/scale.test.ts`) | 1,000 orders/day × 63 days (63,000 orders, items, profit lines), Etsy + Amazon | `buildDigest` **330 ms**, status `ready` | 60 s |
| Digest AC29, sweep (same file) | 1,000 Phoenix shops, 3 orders each, all due at Mon 07:05 | `sweep` **15.2 s**, 1,000 built, 0 failed; second sweep built **0** (no duplicates) | 30 min |
| Market AC28 (`MARKET_SCALE=1 vitest run src/modules/market/market-scale.acceptance.test.ts`, new QA file) | 5,000 active designs, 584,000 orders / 1,168,000 items over 156 weeks (≈1,070 units/day, Q4 skew), 96,264 profit lines (90 d), Etsy + Amazon connected, mock sources; fixture built in 40.4 s | `refreshDemand` **4.4 s**; `computeSignalsForShop` **7.8 s** (5,000 designs mapped by stems, 15,470 signals, 0 recommendations on the uniform series); re-run 7.5 s, 0 new recommendations | 15 min |

T-18-3's own synthetic run (12.2 s) used a scratchpad fixture that no longer exists; the new file makes AC28 repeatable and is the third opt-in scale check next to `scale.test.ts`. No k6 arrival-rate scenarios this wave (no new interactive hot path; the digest is a job).

## 7. Screenshots (`invai-docs/waves/19/reviews/gate-shots/`, looked at)

1. `01-today-digest-card-en-1440.png` — Today with the card "Your week in review is ready · $652.92 (-37.9%)", "Email me every week" (owner was opted out by the browser suite at shot time) and "See this week"; KPIs Due today 39 / Overdue 14 / At risk 31 / Blocked 10 / On vendor 2 / Low stock 9; station board and alerts render.
2. `02-digest-page-es-390.png` — the digest at phone width in Spanish: banner "Los números son estimados: las comisiones de 81 pedidos aún no son finales.", opt-in card "¿Quieres recibir esto en tu correo cada lunes?", Ingresos $1,956.37 ↓-50.8 %, Ganancia neta $652.92 ↓-37.9 %, Margen 33.4 % ↑+26 %, Pedidos 35 ↓-52.1 %, Tasa de puntualidad 100 % ↑0 %, Uso del plan. USD stays "$". Heading reads **"Semana del Mon, Sep 21"** (issue 2).
3. `03-settings-notifications-en-1440.png` — "Weekly review · Every Monday at 7:00 AM, Mountain Standard Time" on, Day/Time selects, "Write the summary with AI" disabled with the shadow explanation, Recipients (Riley Owner / Alex Admin / Olivia Office, "Email works", "Not by email"), "Send me a preview now".
4. `04-unsubscribe-en-1440.png` — public page "Manage your weekly review email · Stop getting the weekly business review by email?" with the red Unsubscribe button; no app shell, no console errors (e2e test 8).
5. `05-mailpit-digest-email.png` — the email as rendered: glance, three action links, Market watch with "Google Trends, Oct 4, 2026", "High confidence", "Sample data".
6. `06-profit-en-1440.png` — Profit (last 30 days): revenue $13,695.39 − costs $9,863.48 = net $3,831.91 ✓, margin 28.0 % ✓ (3831.91 / 13695.39); chart and table agree (Cactus Mama $224.32).

No `##` order numbers, no raw i18n keys, images load.

## Issues, ranked (owner in brackets)

1. **Medium — Market watch recommends acting before a month that has passed.** Both Market watch items in the seed digest and email read "List Teacher Of Tiny Cacti … and stock … **before September**." on Sep 28; the rows carry `params.peakMonth 9`, `actByDate 2026-08-04` (past), band `high`. `market-watch.ts` (T-19-3) takes the top-band R1 rows without dropping ones whose act-by date or peak month is already behind, so a shop is told to prepare for a peak that is over (sibling of wave 18 issue 5 "Act by in the past"; the digest turns it into advice). Suggested: skip recommendations with `actByDate < weekEnd` (or peak month past) in the Market watch pick, and let the market rule not emit them [backend-engineer (digest) for the filter; backend-engineer (market) for R1; PM for the wording rule]. Evidence: `dg-owner.json` marketWatch, `market_recommendations` rows for the two ids.
2. **Low — Spanish digest heading uses an English date.** `/digests/2026-W39` in es renders "Semana del **Mon, Sep 21**" while the list row and everything else is Spanish (the T-19-5 round-2 fix covered the market dates and `sourceDateText`, not the page title / list row range). [web-engineer, `invai-web/src/components/digest/digest-copy.ts` or the digests route title]. Screenshot 2.
3. **Low — change copy for a flat metric and for a percentage-point metric.** "Shipped on time: 100% (0% vs last week)" (email) and "↑ 0%" with a green up arrow (web) for no change; "Margin: 33.4% (+26% vs last week)" is a relative change of a percentage (26.5 → 33.4) that reads like +26 points. Spec copy table; suggest "unchanged" / "sin cambio" and "+6.9 pts" for `marginPct` [product-manager for the rule; backend-engineer (digest) `render.ts` and web-engineer `digest-copy.ts` to apply].
4. **Low — source date in the future.** Email: "Google Trends, Oct 4, 2026"; web: "Google Trends, week ending Oct 4". `market_signals.as_of` for every mock outside source is the end of the *current* ISO week (2026-10-04 on a Monday gate; it was 2026-09-27 on Sunday's wave-18 gate). The web wording makes it readable; the email's `date` fact formatter does not. Pre-existing from wave 18's mock sources [backend-engineer (market) for the mock `asOf`; backend-engineer (digest) if the email should say "week ending"].
5. **Low — pre-existing, still visible:** Today alert body "Ship-by was 2026-09-26T06:59:59.999Z and no label has been bought." (wave 18 issue 4) [backend-engineer, today]; the refused Notifications page shows the raw "Missing permission org.manage for digest.settings.get" (noted in `digest.spec.ts`, `errorInfo()` has no `FORBIDDEN` case) [web-engineer]; plan usage renders "10000" without a thousands separator [web-engineer, cosmetic].
6. **Informational:** `win` is `null` on the seed digest (no D8 win fired; the page simply omits the block). `incompleteOrders 81` counts week orders with items but no profit line yet (unshipped), so "fees for 81 orders aren't final" sits next to "Orders: 35" (orders with profit lines) — consistent with the profit page's own "some orders have no fee data yet", but a reader may wonder. The stale-job replay after `db:reset` (section 3) is worth a line in the runbook [platform-sre/docs-writer].
7. **QA follow-ups (mine, uncommitted in this run, for the tech lead to fold in or ask me to commit):** `invai-web/e2e/digest.spec.ts` selector fix (section 4); new `invai-backend/src/modules/market/market-scale.acceptance.test.ts` (AC28, opt-in `MARKET_SCALE=1`). Full repo checks re-run after these edits at 09:22–09:27: backend `pnpm typecheck && pnpm lint && pnpm test` → 130 files passed, 2 skipped / 1068 tests passed, 3 skipped, 1 todo (exit 0; the new skip is the opt-in scale file); web `pnpm typecheck && pnpm lint && pnpm test && VITE_API_URL=http://localhost:3000 pnpm build` → 97/97, build ok (exit 0). `qa-report.md` §AC28/§AC29 updated with the numbers.

No bugs filed against T-19-1..5's own acceptance criteria.

## Processes and data

- Started and stopped by recorded PID: imaging 46343 (listener 46359), web 46344 (46360), floor 46345 (46361), worker 46555 (killed first, before the reseed). Verified afterwards: nothing on 8000/5173/5174, no `tsx watch src/worker`, no uvicorn, no vite; only pids 40324 (`:3000`), 40321 (`:3142`) and 40322 (`:3178`) listen, all pre-existing and untouched.
- Docker infra left running, healthy. `invai_t19_qa_scale` dropped; Redis DB 15 flushed.
- Shared dev DB: reset, migrated and seeded at 08:59 for the gate; **reset, migrated and seeded again at 09:20** after the run (`[seed] done {"orders":360,"items":670,"transitions":3871,"dueSoon":88,"seconds":23}`, imaging up, worker stopped), so it holds no digest, no notification preference and no golden-path orders. `seed-output.json` written by the seed, not by hand.
- Temporary screenshot specs (`invai-web/e2e/_gate-shots*.spec.ts`) removed; `git status --short`: contracts and floor clean; backend `?? src/modules/market/market-scale.acceptance.test.ts`; web ` M e2e/digest.spec.ts`. Nothing committed or pushed. Mailpit keeps the digest email (id `2Od28hwv91ZEQKMvkP2x2N`) for the tech lead to open.
