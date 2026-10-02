---
name: misc-safety-and-review-notes
description: PID-kill safety, an authz bucketing classification shortcut, and a docs-inconsistency review example
metadata:
  type: feedback
---

- **PID-kill safety (T-P3-1).** Killed a PID (31268) believing it was my own `tsx src/api/server.ts`
  child because the command line and elapsed time matched loosely — it was actually a different
  session's dev API on a different port (:3142, not my :3136). Before killing anything you didn't
  capture `$!` for yourself, confirm with `lsof -p <pid> -a -iTCP -sTCP:LISTEN` that the port
  matches what you started, not just the command string.
- **`bucketFor` priority chain classification (T-P3-1, B-236).** `bucketFor`'s priority chain
  (`ai` check, then `station`, then GET) means a procedure's own meta (e.g. `ai.validate`'s
  `ai.listings.read` permission) is irrelevant once an earlier branch already claims it — don't
  re-bucket anything the card's AC says is "unchanged" even if it superficially matches a new rule.
  Classifying "is this handler really a read" is cheap with
  `grep -n "insert(\|update(\|\.values(\|putObject\|getSupplierAdapter\|renderValues" <service.ts>`
  right after the router line — every false "read" found (preview, suppliers.stock,
  batchLabelPdf, exportCsv, analytics.export) called `putObject`/an outbound adapter/imaging,
  visible in under 5 lines of context.
- **Self-contradicting docs are a real review finding (T-19-1).** An ADR/README that says "GET
  never mutates" and then describes a GET click-recording write in the same breath licenses two
  different implementations — flag it, don't dismiss as nitpicking. The right fix is usually to
  narrow the absolute claim to the security-sensitive case (unsubscribe) and name the benign write
  (click record) as an intentional, idempotent exception, rather than deleting one side. Also: a
  company-keyed `checkRateLimit(bucket, companyId)` token bucket generalizes to an IP-keyed bucket
  for free (the second arg is just an opaque string) — no new limiter mechanism needed for
  auth-less routes.
