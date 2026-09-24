---
name: scale-test
description: Load-test InvAI against small, mid and large multi-tenant seed profiles with k6 arrival-rate scenarios whose thresholds are the p95 SLOs from research 11 (order list, CSV import, sheet build, label batch, floor scan), plus EXPLAIN checks under RLS. Use before a stage transition or pilot, after a change to a hot path, or for "load test", "performance", "p95", "k6", "scale seed", "will it hold".
---

# Scale test

A repeatable load run that says, with numbers, whether InvAI meets its p95 targets at a given shop count and size mix, and which layer breaks first.

## When to use
- Before each stage transition (pilot → growth, research 11 §1) and before a pilot goes live.
- After changing a hot path: order list and filters, import, sheet build, label batch, floor scan, RLS policies or indexes.
- Owners: qa-engineer (k6 scripts, scale seed profiles, the report); backend-foundation (seed code location, DB fixes); imaging-engineer (compose budget); platform-sre (staging environment).

## Current state (verify first)
- The only seed is the one demo shop (`pnpm db:seed`, roughly 15–20 minutes per runbook §4, mostly imaging renders, `src/db/seed/index.ts`). Scale profiles don't exist: `pnpm db:seed:scale --profile small|mid|large` and `invai-backend/src/db/seed/scale/` are **to be created** (backlog B-34, location agreed with backend-foundation).
- No k6 scripts exist; proposed home `invai-web/e2e/load/` (to be created, QA-owned). k6 is not installed on this machine (`which k6` is empty): use `brew install k6` or `docker run --rm -i -v "$PWD":/w grafana/k6 run /w/<script>.js` (inside Docker, the API is `http://host.docker.internal:<port>`).
- The API has no per-tenant rate limit and imaging has no compose concurrency limit yet (research 11 G13, G15), so expect the first failures there.

## Steps
1. **Pick the profile** from `profiles.md` (this folder) and write the question in the card: "Does pilot-scale (small) meet all p95 targets with 2× peak?"
2. **Seed a separate database**, never the shared dev DB. The seed must be realistic: the size mix from the demo seed (adult 10.5×12, youth 8.5×9.5, chest 3.75, sleeve 3×10, back 12×14 in), skewed tenant sizes, 12 months of history for `large`, enough stock that nothing goes negative, and PII fields filled with fake data only.
3. **Run under RLS as the app.** The API must connect as `invai_app` through `withTenant`; results measured as the owner role are invalid because RLS changes plans.
4. **EXPLAIN the top queries** before loading: for `orders.list` with its filters, `today.summary`, the ship queue and the station queue, run `EXPLAIN (ANALYZE, BUFFERS)` as `invai_app` with `app.company_id` set to a large and a small tenant. No sequential scan on large tables; indexes lead with `company_id`; watch the trigram GIN indexes that span all tenants (research 11 G17).
5. **Write k6 scenarios with arrival-rate executors** (open model, `constant-arrival-rate` / `ramping-arrival-rate`), one per load shape (research 11 §6.2), with the SLOs as `thresholds` so the run fails when a budget is missed:
   1. floor scan storm: 20 stations × 1 scan per 3 s per shop (`production.scan`, floor session, unique `clientScanId` per scan);
   2. order import burst at 10× normal (`channels.importCsv` with generated CSVs, or Shopify webhooks with valid HMAC against the mock secret locally);
   3. sheet build for 5 tenants at once (`production.batches.build`, then poll the job);
   4. label batch (`shipping.batchBuy`, mock carrier);
   5. dashboard reads (`today.summary`, `orders.list` with filters and cursor paging).
   Sign in once per virtual user role in `setup()` (`POST /api/auth/sign-in/email` with an `origin` header, as `invai-web/e2e/helpers/api.ts` does); spread load across tenants with the profile's skew.
6. **Run** the steady scenario for at least 10 minutes, then a breakpoint run (ramping arrival rate until thresholds fail). Record the arrival rate at the break.
7. **Watch the server side** during the run: API and worker logs, BullMQ waiting counts and oldest-job age per queue, outbox backlog (`outboxBacklog()` in `src/worker/outbox-relay.ts`), Postgres connections (7 processes × 14 pool slots ≈ 98 in AWS terms, research 11 §2.2), imaging RSS.
8. **Find the first bottleneck** with `root-cause-bug`'s layer bisection and file it to the owner with the numbers. Don't tune in the same card unless you own the layer.
9. **Report** in `invai-docs/build/qa-report.md`: profile, commit SHAs of every repo, machine, each scenario's p50/p95/p99 and error rate vs threshold, breakpoint capacity, EXPLAIN findings, bottleneck and filed cards. Capacity for a stage transition also goes to the runbook through docs-writer.

## Targets (thresholds)
| Scenario | p95 target | Source |
|---|---|---|
| Interactive API procedures (`orders.list`, `today.summary`) | < 400 ms | research 11 §5.3 |
| Floor scan-to-result (`production.scan`) | < 300 ms (SHOULD < 150 ms) | research 11 §5.3; research 12 §3.9 |
| Label purchase job, enqueued → done | < 60 s | research 11 §5.3 |
| Gang-sheet compose, enqueued → file ready (240 in sheet) | < 5 min | research 11 §5.3 |
| API availability during the run | ≥ 99.5% non-5xx | research 11 §5.3 |
| Nightly regression | fail if p95 rises > 20% over the last baseline | research 12 §3.9 |
The CSV import target is not set in the research: record the baseline (rows per second, time to `import.completed`) and propose a target to the tech lead.

## Rules (MUST / MUST NOT)
- MUST use arrival-rate (open-model) executors; closed-model VU loops hide latency under load.
- MUST NOT load-test real marketplaces, EasyPost or Anthropic; mocks only (no keys exist anyway).
- MUST NOT run against the shared dev DB or while other agents need the machine; stop every process you started.
- MUST keep thresholds equal to the SLO table; changing a target is a tech-lead decision, not a script edit.

## Done when
- The profile was seeded, EXPLAIN checks recorded, and every scenario ran with thresholds evaluated.
- `qa-report.md` has the table of results, the breakpoint, the SHAs and the filed bottlenecks.
- Processes stopped and the scratch database dropped or left documented.

## References
- `profiles.md` (this folder)
- `invai-docs/research/11-platform-scale-playbook.md` §1, §2.1–2.2, §5.3, §6.1–6.2, §10
- `invai-docs/research/12-security-quality-playbook.md` §3.9
- `invai-docs/waves/backlog.md` B-34; `.claude/agents/qa-engineer.md`, `backend-foundation.md` (seed rules)
- Related: `root-cause-bug`, `imaging-change-with-budget`, `run-golden-path`, `define-slo`
