# Wave 18 integration gate

Reviewer: qa-engineer, on Fable 5.1. Ran 2026-09-27 16:25–17:05 (America/Phoenix).

Commits under test (local, not pushed):
- invai-contracts `378d6ae` (0.6.1)
- invai-backend `0bc68e2`
- invai-web `127ef08`
- invai-floor `68b9cbb` (no wave-18 commits; contract consumer)

Cards T-18-1..5, all approved (reviews in `invai-docs/waves/18/reviews/T-18-*`).

## Verdict

**PASS with one filed Medium bug (not a wave-18 card).** Every repo check is green; API golden path 13/13, floor 3/3, screens smoke 2/2 and market 5/5 are green on one fresh seed; the market jobs ran through the worker's own scheduler and the three starters answer in English and Spanish with sources, dates, "Sample data" and vote cards; designer@ is refused.

The one red result is the **full `pnpm e2e` run in `invai-web`**, which fails on a fresh seed because the suite's own assistant traffic exhausts the per-company `ai` rate bucket (20/min) that cheap `ai.*` reads share with model calls (issue 1 below). Each suite passes on its own, and the same traffic pattern hits a real owner. The tech lead decides whether to push with issue 1 as a card; my recommendation is push, with issue 1 as a wave-19 card for backend-foundation/architect, since it predates wave 18 (T-12-3) and wave 18 only made it visible.

## 1. Pre-checks — PASS

- `@invai/contracts` links: backend, web and floor all `-> ../../../invai-contracts`.
- `df -h /`: 228Gi total, **15Gi available**.
- Infra: `local-postgres-1`, `local-valkey-1`, `local-minio-1`, `local-mailpit-1` all `Up (healthy)`.
- Processes before start: `:3000` = pid 75936 (`tsx watch src/api/server.ts`, started Sep 27 11:51, not mine; health `ok`, serves the new code: `market.niches.taxonomy` answers 100+ niches signed in as owner). `:3142` = pid 75935 (orphan, left alone). No worker, imaging, web or floor running. All git trees clean.

## 2. Repo checks — PASS (all four repos)

| Repo | Command | Result |
|---|---|---|
| invai-contracts | `pnpm typecheck && pnpm lint && pnpm test` | tsc clean; biome clean; **6 files / 52 tests passed** |
| invai-backend | `pnpm typecheck && pnpm lint && pnpm test` | tsc clean; biome 343 files clean; **114 files / 928 tests passed** (196.8 s, on `invai_test`) |
| invai-web | `pnpm typecheck && pnpm lint && pnpm test && VITE_API_URL=http://localhost:3000 pnpm build` | tsc clean; biome 154 files clean; **16 files / 88 tests passed**; build `✓ built in 1.30s` (one >500 kB chunk warning, non-blocking) |
| invai-floor | `pnpm typecheck && pnpm lint && pnpm test && VITE_API_URL=http://localhost:3000 pnpm build` | tsc clean; biome 76 files clean; **9 files / 96 tests passed**; build ok (`precache 15 entries`). Bare `pnpm build` fails on the intentional `VITE_API_URL must be set` guard, same as web (no local `.env`; environment, not a bug) |

## 3. Fresh seed — PASS

Started imaging (`uv run uvicorn app.main:app --port 8000`, pid 1727→1770), web (pid 1730, :5173) and floor (pid 1733, :5174); health `{"ok":true,"vips_version":"8.18.6"}`, web 200, floor 200. With imaging up and no worker: `pnpm db:reset && pnpm db:migrate && pnpm db:seed` → `[migrate] up to date`, seed done (`seed-output.json` written 16:30 by the seed). Then the worker fresh: `MOCK_CARRIER_TRANSIT_HOURS=0.001 pnpm dev:worker` (pid 1921). API health after seed: `{"ok":true,"db":true,"redis":true,"imaging":true,"s3":true}`.

## 4. Golden path — API PASS, floor PASS, browser: suites PASS alone, full run FAIL (issue 1)

**API golden path** (`E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts`): **13/13 passed (14.5 s)**. Sheet utilization `[0.8699, 0.8212]`, lengths `[238.76, 76.72]`.

**Full browser run** (`pnpm e2e`, first attempt, right after the API suite): **14 passed, 2 failed, 4 did not run (1.3 m)**.
- `market.spec.ts:129 a vote is stored once…` failed with the test's own message "no starter question produced a recommendation on the seed". That message is wrong about the cause: the trace shows the page state `Something went wrong: Too many requests` and, per `/rpc/ai/*` request in the trace: `assistant/ask` 1×200 then 2×429, `assistant/conversations` 1×200 + 3×429, `credits/balance` 4×429. The serial group then skipped the remaining 3 market tests.
- `screens.smoke.spec.ts:44 every shop screen renders…` failed on `/settings/billing`: `429 POST /rpc/ai/credits/ledger` (request + console error).
- Root cause (backend, pre-existing): `bucketFor` in `invai-backend/src/api/orpc.ts` puts every `ai.*` path into the `ai` bucket (`perMinute(20)`, `src/lib/ratelimit.ts`), so the assistant page's `ai.assistant.conversations` and `ai.credits.balance` refreshes on every ask and reload, and Billing's `ai.credits.ledger`, spend the same 20 tokens as model calls. Golden-path step 12 + market test 1 + the vote test's asks are enough to drain it inside one minute.
- Isolated re-runs, one fresh-seed stack, no reseed, spaced ≥ 1 min apart so the bucket refilled: `pnpm exec playwright test e2e/screens.smoke.spec.ts` → **2/2 passed (16.1 s), "No screen issues."**; `pnpm exec playwright test e2e/market.spec.ts` → **5/5 passed (9.1 s)** (chips + Sample data badge + vote cards; vote stored once and survives reload; Spanish starter/chips/badge; niche chip 0/1/2 and refuses a third; designer changes a niche but sees no votes or prices). `golden-path.spec.ts` passed 13/13 inside the full run.
- Not a retry-to-green: the full-suite failure is recorded as the result it is; the isolated runs are the feature evidence.

**Floor tablet suite** (`pnpm e2e` in `invai-floor`): **3/3 passed (9.6 s)**: pack blocks a missing unit, offline replay parks a rejected scan, station setup / PIN / press check / QC / pack.

## 5. Market on the fresh seed — PASS

- Jobs ran through the worker's own scheduler, no inline run needed: `bull:reports:repeat:market-sweep` (every 3600000 ms, iteration count 2) queued demand → pricing → signals → track within a minute of the worker starting; recommendations created 16:31:06 local. Worker log: 41 `market signals computed` lines (1 shop-wide, 40 design-scoped from `design.updated`).
- Rows: `market_design_niches` 40, `market_signals` 482 (trend 273, seasonality 208, lead_time 1), `market_recommendations` 12 (R1 high 6, R1 medium 6, all `mock=true`), `market_price_snapshots` 0 (seed's Amazon is `csv_only`), `market_series_cache` 139,984.
- Owner asks through `POST /rpc/ai/assistant/ask` (SSE), then the same in the browser:
  - "Which of my designs are trending?" → `get_market_trend`, `mock: true`, sources own + google_trends + pinterest_trends + jungle_scout with `asOf 2026-09-27`; every outside fact reads "Google Trends, as of 2026-09-27 (Sample data)". 0 recommendations (own history under 13 weekly points on the seed, B-130).
  - "Am I priced right on Amazon?" → `get_price_position` (`available: false`: "Amazon isn't connected, so I can't compare prices there") + `simulate_price` on own costs: $23.99 → net $7.97, 33.2 % (7.97/23.99 = 33.2 % ✓); $25.99 → $9.63, 37.1 % ✓; break-even $12.60, floor (15 %) $14.99. No mock, no recommendations (expected on this seed).
  - "When should I get ready for the holidays?" → `get_seasonality`, sources census (asOf 2025-12-31, mock) + google_trends (2026-09-27, mock); summary "Seasonality: 5 of 8 with a peak, 1 to act on now"; **3 recommendations** (R1 medium/high/medium, mock) carried in the `tool_result` event; each recommendation's text ends "Sample data, not your real market: no market source is connected yet." and shows its band ("High confidence", "Medium confidence: test it").
  - Spanish "¿Cuándo debo prepararme para las fiestas?" → same tool, answer fully Spanish ("temporada alta en diciembre", "Datos de muestra", "Confianza media: pruébalo", "Actúa antes del 2026-11-03"), 3 recommendations, vote buttons "Hecho" / "No me sirve" with `aria-pressed` on the one voted earlier by the suite (AC33).
- designer@: `market.recommendations.list` → `FORBIDDEN` (`finance.read`); `market.recommendations.vote` → `FORBIDDEN`; `market.niches.taxonomy` → allowed. Owner `recommendations.list` → 12.

## 6. Screenshots (`invai-docs/waves/18/reviews/gate-shots/`)

1. `01-assistant-holidays-en-1440.png` — Seasonality chip + "Sample data" badge, per-design peaks with source and date, 3 recommendations, vote card with "Medium confidence: test it" + "Sample data" badges.
2. `02-assistant-fiestas-es-390.png` — the same in Spanish at phone width, no overflow, "Datos de muestra".
3. `03-design-niche-chip-1440.png` — Desert Bloom Logo, chip "Niche: Gardening and plants" + Change; thumbnail renders (3150×3600 loaded).
4. `04-today-1440.png` — Due today 34, Overdue 44, At risk 30, Blocked 9, On vendor 2, Low stock 9; station board and alerts.
5. `05-gang-sheet-1440.png` — 2026-09-27 #1, 22″ × 238.8″, film use 87 %, 42 transfers, $71.63, preview renders.
6. `06-profit-1440.png` — Revenue $13,710.39 − costs $9,799.58 = net $3,910.81, margin 28.5 % ✓; chart bars match the table (Cactus Mama $253.17).

Looked at, in both languages: no `##` order numbers, no raw i18n keys, images load. Wrong-looking things are listed below.

## Issues, ranked (owner in brackets)

1. **Medium — cheap `ai.*` reads share the 20/min `ai` rate bucket with model calls** [backend-foundation for `src/api/orpc.ts` `bucketFor`; architect for the bucket policy]. An owner who asks the assistant a handful of questions in a minute gets "Something went wrong: Too many requests" (the whole chat pane resets to the empty state and the just-streamed answer is gone) and a 429 on Billing's credit ledger. Breaks the full `pnpm e2e` on a fresh seed (evidence above). Pre-existing from T-12-3; QA already noted it in `market.spec.ts`; now gate-visible. Suggested fix: route `ai.credits.*` reads and `ai.assistant.conversations`/`conversation` to the `reads` bucket, keep `ask` and generation in `ai`. Secondary, same symptom [web-engineer]: a failed sidebar/credits read shouldn't replace the chat pane with the error state.
2. **Low — assistant answers show raw markdown** (`**Cactus Mama**`, `_(Demo mode…)_`) because `assistant.tsx` renders `m.text` as plain pre-wrap text while the code-written answers emit `**`/`_` (since v1, `197b6b4`; wave 18's market answers inherit it) [ai-engineer + web-engineer: pick one side; either stop emitting markdown or render it].
3. **Low — "_(Demo mode: answer composed from your live shop data without a model call.)_" stays English in Spanish answers** (v1 footer) [ai-engineer].
4. **Low — Today alert body shows a raw ISO timestamp**: "Ship-by was 2026-09-26T06:59:59.999Z and no label has been bought." (`invai-backend/src/modules/today/service.ts:316`; pre-existing) [backend-engineer, today].
5. **Low — seasonality "Act by" in the past**: "Pumpkin Spice Desert … Act by 2026-08-04: 0 weeks to the peak … Act now." shows a past date next to "Act now" [backend-engineer, market; PM to confirm the wording rule].
6. **Informational** — trend answers: designs in the same niche get identical mock numbers (Vintage Route 66 Diner and Good Vibes Only Agave both "+5.5 % over 4 weeks, +259.1 % year over year") and a "+259 % YoY" is labelled "flat" (the label follows the ±15 %/4-week rule). Per spec; a reader may find it odd. Price position never fires on the seed (Amazon `csv_only`), so R2/R4 are only proven by the backend acceptance tests (B-130).
7. **QA follow-ups (mine, next QA pass, not in these commits):** `market.spec.ts` es test expects vote-button names ending "no me sirve" but the es aria-label ends "como que no sirve", and it asks the trending starter, which has no recommendations on the seed, so Spanish vote cards are never asserted; `firstAnswerWithVotes` should fail with the 429 text instead of blaming the seed.

No bugs filed against T-18-1..5's own acceptance criteria.

## Processes and data

- Started and stopped by recorded PID: imaging 1727 (listener 1770 via `lsof -ti :8000`), web 1730 (listener via `lsof -ti :5173`), floor 1733 (`lsof -ti :5174`), worker 1921 and its `tsx watch` child (gone after the kill; read-only `ps` check empty). Verified afterwards: only pids 75936 (`:3000`) and 75935 (`:3142`) listen, both pre-existing and untouched.
- Docker infra left running, healthy.
- Shared dev DB: reset, migrated and seeded at 16:30 for the gate; **reset, migrated and seeded again at 17:02** after the run (`[seed] done {"orders":360,"items":687,"transitions":3897,"dueSoon":88,"seconds":24}`, imaging up, worker stopped), so it is freshly seeded with no market rows (the next worker's sweep fills them within a minute). `seed-output.json` written by the seed, not by hand.
- Temporary screenshot specs (`invai-web/e2e/_gate-shots*.spec.ts`) deleted; `git status --short` clean in all four repos. Nothing committed or pushed.
