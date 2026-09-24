---
name: add-observability
description: Make an InvAI code path observable — scoped structured logs with company_id, request_id and trace_id and no PII, error capture, trace context from API through outbox and BullMQ to imaging, and each new alert with threshold, owner and runbook link. Use when adding a procedure, job, webhook or integration, for the observability baseline (B-18), or after "we couldn't tell what happened".
---

# Add observability

When something breaks for one shop, we can find its requests, jobs and renders by `company_id` and trace id,
see the error, and get paged by an alert that says what to do, without any buyer PII in the logs.

## When to use
- A card adds a procedure, job, webhook handler, integration call or imaging endpoint (the owner of that path
  adds the logs).
- The observability baseline and its follow-ups (backlog B-18, research 11 G14, research 12 G7):
  backend-foundation for `src/lib`/`src/api`/`src/worker`, imaging-engineer for `invai-imaging`, platform-sre
  for `invai-infra` and alerts.
- After an incident where the logs couldn't answer "which shops, since when".

## What exists (2026-09-24)
- `invai-backend/src/lib/log.ts`: `logger("<scope>")` with `debug/info/warn/error(msg, data)`, JSON lines in
  production, plus `errorData(err)`. No redaction layer.
- `requestId` is created per request in `src/api/context.ts` but never logged. No access log, no
  OpenTelemetry, no metrics.
- The worker logs `job failed` with queue, job name, id and attempts, not the tenant (`src/worker/index.ts`).
- `/health` on the API and imaging. No error tracker, no alerting, no central log store.

## Steps
1. **Log through the scoped logger,** never bare `console.*`: `const log = logger("<module>")`. Each line has
   a fixed message (`"label purchased"`, not an interpolated string) and a data object.
2. **Always include the context fields** you have: `companyId`, and the entity ids (`orderId`, `orderItemId`,
   `sheetId`, `shipmentId`, `jobId`, `connectionId`), plus `requestId` in request code (from the oRPC context)
   and `queue`/`job` in workers. Once the baseline lands (B-18), these come from `AsyncLocalStorage`
   automatically; until then, pass them.
3. **Never log PII or secrets.** Not buyer name, email, phone, street, city, zip, buyer notes, personalization
   text, tokens, cookies, API keys, full webhook bodies, SQL parameters (Drizzle errors include them: S-29).
   Log ids and counts instead. Wrap errors with `errorData(err)` and don't attach the raw object.
4. **Choose levels by action:** `error` = someone must act (a job failed permanently, a webhook signature
   failed); `warn` = degraded but handled (retry, fail-open fallback such as the PIN lockout's Redis timeout,
   S-06); `info` = business events worth counting; `debug` = development only.
5. **Carry trace context** (baseline design, research 11 §5.2; build it where it's missing):
   - API: OpenTelemetry Node SDK with HTTP, pg, ioredis and BullMQ instrumentation (to be added).
   - `emit()` in `src/lib/outbox.ts` stores the W3C `traceparent` in the outbox payload metadata; the relay
     copies it into job data; the worker extracts it; calls to imaging send it as an HTTP header; imaging uses
     FastAPI instrumentation (to be added).
   - `company_id` goes on every span as an attribute, never as a metric label on high-volume CloudWatch
     metrics.
6. **Capture errors.** Unexpected errors in procedures and jobs are logged once at `error` with context. No
   error-tracking service is chosen yet: picking one is an `ops` decision (`record-decision`) and a spend
   question for the owner (`escalate-to-owner`).
7. **Add or update an alert** when the path can fail in a way someone must act on. Write it in
   `invai-docs/ops/alerts.md` (to be created, platform-sre owns it):
   ```
   ## <alert-name>
   - Signal and query: <metric or log query>
   - Threshold and window: <for example failed-set growth > 20 in 15 min on queue ship>
   - Severity: page / ticket   Owner: <role>   SLO: <link or "data safety">
   - First 5 commands: <what to run first, with real paths>
   - Runbook: incident-response; related decision or card
   ```
   Page only on SLO burn (`define-slo`) and data-safety alarms (parked outbox events, backup failure, RDS
   storage > 85%, Valkey memory > 80%, AI spend breaker, failed PII purge, webhook signature failures).
8. **Verify locally.**
   - Run the path on your own API port with `LOG_LEVEL=debug`, and check the lines have the fields from step
     2.
   - For JSON output as in production, run with `NODE_ENV=production` only in a throwaway shell and never
     against real keys.
   - **PII check:** after exercising the path with seed or golden-path data, grep your captured log output for
     buyer data from the fixture you used, for example
     `grep -Ei "maria gonzalez|camelback|@example\.com" <log file>`; it must print nothing.

## Rules
- MUST tag logs with `companyId` wherever a tenant is known (research 11 rule 9).
- MUST NOT log PII, secrets or full payloads, at any level.
- MUST NOT use `company_id` as a CloudWatch metric dimension on high-volume metrics (cost grows per value);
  query logs and traces per tenant instead.
- MUST NOT add an alert without an owner, a threshold and first commands. An alert nobody can act on is noise.
- App-side logging changes live in their owner's paths; platform-sre changes `invai-infra` and
  `invai-docs/ops/**` only (`respect-ownership`).

## Done when
- New code logs through `logger()` with context ids and no PII; the PII grep printed nothing.
- New failure modes that need action have an entry in `invai-docs/ops/alerts.md` with owner, threshold and
  first commands.
- For baseline work: a request's trace id can be followed from the API log line to the job and the imaging
  call.

## References
- `invai-docs/research/11-platform-scale-playbook.md` §5 (observability, SLO alerting), §10 G14
- `invai-docs/research/12-security-quality-playbook.md` §1.10 (audit logging, redaction, alerts, fail closed)
- `invai-backend/src/lib/log.ts`, `src/api/context.ts`, `src/lib/outbox.ts`, `src/worker/index.ts`,
  `src/worker/outbox-relay.ts` (`outboxBacklog()`)
- Related: `define-slo`, `incident-response`, `record-decision`
