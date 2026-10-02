---
name: ta5-savepoint-market-call
description: Pattern for reviewing analytics code that calls another module's service mid-transaction (e.g. analytics.designLifecycle calling market.getTrendSignal)
metadata:
  type: project
---

T-A5 (`invai-backend/src/modules/analytics/design-service.ts`) calls the market module's
`getTrendSignal` from inside `designLifecycle` via `tx.transaction((sp) => getTrendSignal(sp, ctx, ...))`
— a savepoint — with the result `.catch()`-ed and logged (no PII) rather than left to abort the
outer transaction.

**Why:** a cross-module read that isn't isolated in a savepoint can abort the whole outer
transaction (and thus the rest of the analytics response) on a transient failure in the other
module; wrapping it also gives a clean point to enforce company_id scoping came from the same
`ctx`, not a fresh unscoped call.

**How to apply:** when a co-review touches analytics or any module that reads another module's
service function mid-request, check for (a) a savepoint or equivalent isolation around the cross-
module call, (b) the same tenant `ctx` passed through (no re-derivation), and (c) a caught/logged
failure path instead of a bare await. Good template to point authors at if a future card lacks
this.
