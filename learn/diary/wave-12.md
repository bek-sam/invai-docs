# Wave 12 — reliable at scale (local)

**Dates:** late September 2026, after wave 9. AWS-specific parts explicitly deferred along
with waves 10 and 11 (decision 0019) — this wave only covers what's provable locally.

## What was built
- **T-12-1** Retries, DLQ, redrive, stuck sweeps (backend-foundation): BullMQ jobs that
  fail retry sensibly, a permanently-failed job gets parked in a dead-letter queue instead
  of vanishing, and a sweep catches jobs stuck mid-run.
- **T-12-2** Health, timeouts, graceful shutdown, migrate lock (backend-foundation):
  `/livez`/`/readyz` tell the truth about the service's real state, and a deploy can shut
  down without dropping in-flight work.
- **T-12-3** Rate limits and queue fairness (backend-foundation): one busy tenant's traffic
  can't starve every other tenant sharing the same queue — enforced with a Valkey-backed
  rate limiter.
- **T-12-4** Tenant export, deletion and retention (backend-foundation + compliance-
  officer): a shop's data can be exported and deleted on request (without KMS yet).
- **T-12-5** CSP and security headers; SVG not served inline (web-engineer + floor-
  engineer): strict security headers on both apps, and uploaded SVGs are never served
  inline (an XSS vector if they were).

## Why
Everything through wave 9 proved the golden path *works*. Wave 12 asks a different
question: what happens when it's under load, when a job fails halfway, when one shop
sends ten times the traffic of everyone else, or when a deploy needs to restart without
corrupting an order mid-write? This is the reliability half of module 06, built for real.

## What went wrong
- The wave file carries forward a blunt instruction in bold: **"Every prompt says 'Don't
  push.'"** This line exists directly because of wave 8's 44-ungated-commits incident (see
  wave 8's diary entry) — by wave 12, the fix isn't just "the tech lead remembers to say
  it," it's written into the wave file itself as a standing rule for every card.
- This wave also folds in follow-up fixes that had been deferred from earlier waves: stuck
  intents and job rows, an outbox job-id override, a final-failure sweep, a Valkey
  fail-open alert, `floor_requests` retention, and the advisory lock around migrate and
  reference data — a sign that "reliable at scale" work accumulates real debt from every
  prior wave's shortcuts, and needs its own dedicated wave to pay it down rather than
  getting squeezed into feature waves.

## What the team learned
- Deferring AWS-specific reliability work (waves 10/11) while still doing everything
  provable *locally* let the team keep moving without waiting on cloud access — reliability
  isn't one monolithic thing; the local half (retries, rate limits, health checks) and the
  cloud half (real autoscaling, real multi-AZ failover) can ship on different schedules.
- A written, bolded rule in the wave file itself is a stronger signal than a rule that
  only lives in a shared playbook — this wave is the direct response to wave 8's push
  mistake, and the "Don't push" line shows up in every wave file from here through the
  rest of the project.

## Files to look at
- `invai-backend/src/lib/queues.ts`, `src/worker/` — retries, DLQ, redrive (T-12-1).
- `invai-backend/src/api/app.ts` (`/livez`, `/readyz`), `src/db/migrate.ts` (the advisory
  lock) — T-12-2.
- `invai-backend/src/lib/rate-limit.ts` (Valkey-backed) — T-12-3.
- `invai-backend/src/modules/tenancy/service.ts` — export/deletion (T-12-4).
- `invai-web`'s and `invai-floor`'s server/middleware config for CSP headers; the SVG
  upload path that stopped serving inline (T-12-5).
- `invai-docs/waves/12/wave.md` — the carried-forward follow-up list and the "Don't push" rule.
