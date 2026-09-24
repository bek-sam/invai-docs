---
name: define-slo
description: Define or change an InvAI SLO — SLI, target, window, measurement source, error budget and multiwindow burn-rate alerts, starting from research 11 §5.3's five (API availability, interactive latency, floor scan, label purchase, gang-sheet compose). Use when setting up monitoring, adding a user-critical flow, reviewing error budgets, or asked "how reliable should this be".
---

# Define an SLO

Each thing a shop depends on has one written, measurable promise with an error budget and alerts that page
only when the promise is really at risk.

## When to use
- Setting up the first SLOs (platform-sre, with the product-manager for targets).
- A new user-critical flow needs a promise (for example marketplace sync freshness).
- The monthly SLO review (tech lead, research 11 §9), or an error budget is spent.

## The starting five (research 11 §5.3)
| # | SLO | SLI (good events / valid events) | Target | Window | Measured by | Source exists? |
|---|---|---|---|---|---|---|
| 1 | API availability | requests not answered with 5xx or an app error / all requests (4xx excluded) | 99.5% | 28 days | ALB 5xx + app error logs | ALB metric only after deploy; app access log to be created (B-18) |
| 2 | API interactive latency | interactive procedure requests faster than 400 ms / all interactive requests | 95% (p95 < 400 ms) | 28 days | access log `duration_ms` per procedure | to be created (B-18) |
| 3 | Floor scan to result | scan requests (procedures with permission `production.scan`, e.g. `scan`, `scanBatch` in `invai-contracts/src/contract/production.ts`) faster than 300 ms / all scan requests | 95% (p95 < 300 ms) | 28 days | access log for those procedures | to be created (B-18) |
| 4 | Label purchase job | label jobs enqueued → done within 60 s / all label jobs | 95% (p95 < 60 s) | 28 days | BullMQ job timings, queue `ship` | to be created |
| 5 | Gang-sheet compose | compose jobs enqueued → file ready within 5 min for a 240" sheet / all compose jobs | 95% (p95 < 5 min) | 28 days | BullMQ job timings, queue `render` | to be created |

Candidates to consider next (not yet agreed): marketplace sync freshness under 15 minutes, label purchase
success rate (research 13 §5.4).

## Steps
1. **Start from the user.** Name the shop person who feels it and the moment ("the presser waits on the scan
   beep", "the packer waits for the label"). No SLO for things nobody waits on.
2. **Write the SLI as a ratio** of good to valid events, with exact inclusions: which procedures count as
   interactive (list them from `invai-contracts/src/contract/`), which status codes are "bad", which job names
   count (`defineJob` names in `invai-backend/src/modules/<area>/jobs.ts`).
3. **Pick target and window.** Start with the research 11 targets. Don't promise 99.9% before there is
   Multi-AZ and a pooler (research 11 §7.1). Targets are a product decision with the PM; any target in a
   contract or on a public page is the owner's call (`escalate-to-owner`).
4. **Compute the error budget.** Budget = 1 − target over the window. 99.5% over 28 days = 0.5% of requests,
   about 3 h 22 min of full outage. For a 95% latency SLI the budget is 5% slow events.
5. **Define the alerts** (multiwindow, multi-burn-rate, research 11 §5.3):
   | Alert | Burn rate | Long window | Short window | Action |
   |---|---|---|---|---|
   | fast burn | 14.4× | 1 h | 5 min | page |
   | slow burn | 6× | 6 h | 30 min | page |
   | budget leak | 1× | 3 days | — | ticket |
   Both windows must exceed the rate for a page. For 99.5%, 14.4× means more than 7.2% bad events; 6× means
   more than 3%.
6. **Name the measurement source** and whether it exists. If it doesn't, add a card for it (usually B-18) and
   mark the SLO "defined, not measured" until it does. A measured SLO needs a query someone can run.
7. **Write it down** in `invai-docs/ops/slos.md` (to be created, platform-sre), one section per SLO:
   ```
   ## SLO-<n>: <name>
   - User and moment: …
   - SLI: good = …; valid = …
   - Target / window: … / 28 days      Error budget: …
   - Source and query: … (status: measured / not yet measured, card …)
   - Alerts: fast burn …, slow burn …, ticket … (entries in ops/alerts.md)
   - Owner: <role>. Reviewed: <date>
   ```
   Add each alert to `invai-docs/ops/alerts.md` through `add-observability`.
8. **Set the budget policy** once (an `ops` decision via `record-decision`): when a budget is spent, the next
   wave carries a reliability card before new features for that area. A spent budget is a planning signal, not
   blame (research 11 §5.3).
9. **Review monthly.** Budget left per SLO, alerts that fired, alerts that should have fired. Change targets
   only through a new decision.

## Rules
- MUST express every SLO as a ratio of events with a target and a window. "Fast" or "reliable" is not an SLO.
- MUST page only on SLO burn and the data-safety alarms listed in research 11 §5.3; no pages on CPU or single
  errors.
- MUST NOT claim an SLO is met without a query result. "Not yet measured" is an honest state.
- MUST NOT publish SLO numbers to shops or on a site without the owner (and compliance-officer for wording).

## Done when
- `invai-docs/ops/slos.md` has each SLO with SLI, target, window, budget, source status, alerts and owner.
- Every alert in it has a matching entry in `invai-docs/ops/alerts.md`.
- Missing measurement sources have cards (named ids).
- The budget policy is a recorded decision.

## References
- `invai-docs/research/11-platform-scale-playbook.md` §5.2–5.3 (SLOs, burn-rate alerts), §6.1 (performance
  budgets), §9 (tech-lead checklist)
- `invai-docs/research/12-security-quality-playbook.md` §3.9 (`floor.scan` p95 under 150 ms as a regression
  budget)
- Google SRE Workbook, "Alerting on SLOs" (research 11 [S25])
- Related: `add-observability`, `incident-response`, `scale-test`
