# Wave 17 integration gate

Reviewer: qa-engineer, on Sonnet 5. Ran 2026-09-27.

Commits under test (local, not pushed):
- invai-contracts `8713a63` (0.5.0)
- invai-backend `97780c1`
- invai-web `11ffbfe`
- invai-floor `68b9cbb` (HEAD at gate time; typecheck-only consumer)

Cards T-17-1..4, all approved (reviews in `invai-docs/waves/17/reviews/T-17-*-r1.md`).

## 1. Pre-checks — PASS

- `@invai/contracts` links: `invai-backend/node_modules/@invai/contracts -> ../../../invai-contracts`,
  `invai-web/node_modules/@invai/contracts -> ../../../invai-contracts`. Both correct.
- `df -h /`: `228Gi total, 19Gi avail` — well over 5 GB.
- Stale processes found and cleaned before starting: a lingering `tsx watch src/api/server.ts` on
  `:3000` (11h+ old) and 6 orphaned `tsx watch src/worker/index.ts` instances (started at various
  times over the prior 11h, no queue/port ownership). Stopped by PID (not `pkill`): 3605, 16766 (api
  chain) and 2270/2420/2661/2808/3648/3757 plus their live children 16769/16771/16772/16774/16778/16780
  (worker chain). Also stopped a stale `pnpm dev` orchestrator (1930/1932) and its web/floor/imaging
  children (1962, 1963, 1789) so a clean `dev:api`/`dev:worker`/web/floor/imaging set could start on the
  standard ports. **Left untouched:** a process on port `3142` (pid 16765, `tsx watch src/api/server.ts`)
  — a 31xx port per the agent brief, so per the rule it was not killed. It was not needed for this gate
  (all gate traffic used :3000) and did not interfere.

## 2. Repo checks — PASS (all four repos)

| Repo | Command | Result |
|---|---|---|
| invai-contracts | `pnpm typecheck && pnpm lint && pnpm test` | tsc clean; biome 49 files clean; **5 test files / 36 tests passed** |
| invai-backend | `pnpm typecheck && pnpm lint && pnpm test` | tsc clean; biome clean; **98 test files / 715 tests passed** (87.3s, own dev DB unaffected — uses `invai_test`) |
| invai-web | `pnpm typecheck && pnpm lint && pnpm test && pnpm build` | tsc clean; biome 145 files clean; **15 test files / 82 tests passed**; `pnpm build` initially failed with `VITE_API_URL must be set` (see note below) — re-ran with `VITE_API_URL=http://localhost:3000 pnpm build` → succeeded (bundle output, one >500kB chunk warning, non-blocking) |
| invai-floor | `pnpm typecheck` (contract consumer only, per instructions) | tsc clean |

**Note (environment, not a code bug):** `invai-web` has no `.env` file locally (only `.env.example`,
which sets `VITE_API_URL=http://localhost:3000`), so a bare `pnpm build` fails fast on the
intentional `requireApiOrigin` guard (CSP `connect-src` pinning, by design). Not a wave-17 regression;
filing as a minor environment-setup gap below rather than a bug against any card.

## 3. Golden path on a fresh seed — PASS (one retry, environmental)

Infra healthy (`docker ps`: postgres/valkey/minio/mailpit all `Up ... (healthy)`). Started imaging
(`:8000`), api (`pnpm dev:api`, `:3000`), web (`:5173`), floor (`:5174`); all four health checks 200/ok.
Seed run with imaging up and worker stopped:
```
pnpm db:reset && pnpm db:migrate && pnpm db:seed
```
`[seed] done {"orders":360,"items":660,"transitions":3853,"dueSoon":88,"seconds":22}`. Restarted api
once and started the worker fresh with `MOCK_CARRIER_TRANSIT_HOURS=0.001` after the seed, per
instructions, so no worker held pre-reset jobs (two Redis-queue leftovers from before the reset — an
`ai.generateListingDrafts` job referencing a pre-reset draft id — failed and exhausted retries
cleanly; harmless, Redis wasn't flushed by `db:reset`, not a wave-17 issue).

**API golden path** (`E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts`): **13/13 passed** (12.1s).
Sheet utilization `0.864`, length `239.93` — over the 80% film-use bar.

**Browser golden path + screens smoke** (`pnpm e2e`, `invai-web`): first run **14/15 passed, 1
failed** — `4. a personalized item shows its proof in the drawer and is approved` hit the 120s test
timeout. The failure screenshot showed the drawer already fully rendered and correct
(`Personalization · Approved`, checkmark, proof thumbnail, full production timeline including a later
sheet build/vendor/receive) — i.e. the assertions the test makes were satisfiable, but something in
the run stalled well past the assertion timeouts before Playwright reported it (test's own reported
duration was 13.0m against a 120s timeout, and the api/worker processes showed no restart or error
around that time). This matches the documented "retry once for a possible stall/restart" rule, not a
product defect: **retried immediately** with `pnpm exec playwright test e2e/golden-path.spec.ts` alone
→ **13/13 passed cleanly** (59.6s total; step 4 in 8.6s). `screens.smoke.spec.ts` passed on the first
run (**2/2**, all 27+ routes plus the vendor portal, "No screen issues.").

Net: **28/28 web + API golden-path assertions green** across both suites, with one flaky rerun
recorded below under "Remaining issues."

## 4. Floor tablet suite — PASS

`pnpm e2e` in `invai-floor`: **3/3 passed** (9.0s) — pack (missing-unit block), offline replay with a
server-rejected scan parked and alerted, and station setup/PIN/press/QC/pack.

## 5. Assistant smoke test — PASS

Browser tooling was unavailable this session (multiple Chrome browsers connected, and the
disambiguation step requires `AskUserQuestion`, which is not in this role's toolset). Verified instead
through the same `ai.assistant.ask` oRPC procedure the web screen calls, signed in as
`owner@desertbloom.test`, as a temporary Playwright spec in `invai-web/e2e/` (deleted after the run, not
committed):

- **Starter question** ("Are my ads paying off?", the `assistant.starter.ads` chip on
  `invai-web/src/routes/_app/assistant.tsx`): called `get_ad_performance`, streamed 35 text-delta
  events, answered with real per-channel ad numbers (Shopify/Etsy/TikTok Shop spend, ROAS, TACoS).
- **Follow-up** ("And only Etsy?"): streamed a full answer mentioning Etsy specifically (143 orders,
  channel breakdown incl. Etsy margin), no crash, no dropped stream, `done` event received both times.

One thing to flag, not block on: the follow-up called `get_orders_summary` + `get_profit` rather than
re-calling `get_ad_performance` scoped to Etsy — i.e. it answered a margin/orders question instead of
narrowing the ad-performance answer to Etsy. This is the **already-recorded T-17-3 known gap** in
`invai-docs/waves/17/wave.md` ("the mock's follow-up turn reuses the previous turn's tools/period from
history"), not a new defect — filing nothing new here.

## Remaining issues (by severity)

- **Low / flaky, environmental — golden-path.spec.ts step 4** stalled past its 120s timeout on the
  first run, then passed cleanly on an immediate retry with the same server processes and no visible
  restart. No repro on the retry; no code or data was wrong in the stalled run's own screenshot.
  Recommend: if this recurs on a future gate, capture the trace (`trace.zip`) at the moment of the next
  occurrence for a real root cause (pending network request, EventSource, or something else keeping the
  page/context alive past the assertion). Not filed against any wave-17 card — it touches the
  personalization/proof drawer, which no T-17 card owns.
- **Low / environment setup — `invai-web` build needs `VITE_API_URL`** set locally (no `.env`,
  `.env.example` has the value). Not a regression; noted so the next gate doesn't lose time on it.
- **Informational — T-17-3 known gap**, already tracked in `wave.md`: assistant follow-up turns don't
  reliably reuse the prior turn's tool/period. No new card needed; owner (ai-engineer/tech lead) already
  has this noted as a grant target.

No bugs filed against T-17-1..4. All four cards' owned-path checks, golden paths and the assistant
smoke test are green.

## Verdict

**PASS.** Ready for the tech lead to push `invai-contracts@8713a63`, `invai-backend@97780c1`,
`invai-web@11ffbfe` (and note `invai-floor@68b9cbb` was typecheck-only, no wave-17 commits to it) to
`main`.

## Processes and data

- Started (this gate) and stopped by PID at the end: imaging `24413`→`24426`, api `24416`→`25724`(final,
  stopped as `25761`/`25762`/`25745` chain), worker `25727` (stopped as `25762`/`25745`), web
  `24815`→`24835`, floor `24818`→`24836`. Verified `lsof -iTCP:3000,5173,5174,8000` empty afterward.
- Left untouched (not mine, on a 31xx port): pid `16765` on `:3142`. Also left three older, unrelated
  `tsx watch src/api/server.ts` processes not bound to any of the gate's ports (`11838`, `9499`, `1960`)
  — not started by this gate and not blocking it; flagging for the tech lead to check whose they are.
- Docker infra (`postgres`, `valkey`, `minio`, `mailpit`) left running, healthy.
- Shared dev DB: reset, migrated and freshly seeded at the start of this gate (`orders: 360, items: 660`);
  left in that seeded state (not reset again after the gate, so the pushed commits' golden path can be
  re-verified against the same data if needed).
- No scratch/scale test databases were created. `invai-web/e2e/_gate-assistant-smoke.spec.ts` (temporary,
  used only for the assistant smoke test) was deleted before finishing; `git status --short` is clean in
  all four repos.
