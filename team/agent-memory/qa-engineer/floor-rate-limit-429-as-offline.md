---
name: floor-rate-limit-429-as-offline
description: A real 429 rate-limit response on the floor app looks identical to a real timeout/offline fallback — check the trace's network tab and Redis token-bucket keys before trusting "offline" UI text as evidence of a network issue.
metadata:
  type: project
---

2026-10-01, P2 gate root-cause (`invai-docs/waves/P2/reports/gate-rootcause.md`): `press.spec.ts`
failed showing the floor app's offline fallback ("Checked on this tablet while offline") on what
looked like a timeout. It was actually an HTTP 429 from the per-company `writes` Redis token
bucket (`invai-backend/src/lib/ratelimit.ts`, `src/api/orpc.ts` `bucketFor`), because
`files.downloadUrl` is REST-POST (correctly, body param) but `bucketFor` buckets by HTTP method
(`GET` → reads, else → writes), so a high-volume pure read gets counted against the 120/min
writes bucket shared with real mutations. The floor client's `toFailure`/`countsAsAttempt`
(`invai-floor/src/outbox/outbox.ts`) treats 429 as retryable/"unavailable", same UI path as a
genuine timeout — so the symptom alone can't distinguish them.

**Why:** the P1 root-cause report (`waves/P1/reports/gate-rootcause.md` §2) spent a full round
guessing imaging-job contention because the server-side duration log (`production.router.ts`)
only logs scans that complete the handler — a 429 is thrown by the `rateLimit` middleware
*before* the handler runs, so it never appears in that log. Looking for a slow/missing log line
is not enough evidence that a request didn't reach the server at all.

**How to apply:** when a floor/web action shows an offline/retry fallback but server scan/job
duration logs show nothing, check (a) the Playwright trace's `*-trace.network` file for the
actual HTTP status of the failing request (not just whether a log line exists), and (b)
`docker exec local-valkey-1 redis-cli HGETALL tb:writes:<companyId>` /
`tb:reads:<companyId>` right after the failure, before the ~120s TTL expires. A near-zero
`writes` bucket with an untouched `reads` bucket points at a bucket-misclassification bug, not a
network/offline/timeout bug. Also: running the same floor or golden-path suite twice in a row
against the same seeded company within ~60s can legitimately drain a 120/min bucket just from
test traffic — don't assume a result is "the fix worked" without checking the bucket wasn't
simply starved by the previous run.

Related: [[press-spec-offline-fallback-investigation]] (if written later with the fix
verification).
