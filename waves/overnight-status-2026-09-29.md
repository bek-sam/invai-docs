# Overnight status, 2026-09-29 (interim owner report)

Plain summary: two waves are finished and pushed, two more are being built, and the plans for the rest are written and reviewed. Nothing was deployed, sent or bought. The main slowdown was the usage limit: agents stopped four times, and the team resumed from what was on disk each time.

## Finished and pushed to `main`
| Wave | What it delivered | Pushed SHAs |
|---|---|---|
| 20 | Digest, market and Today copy correct on real dates (no "stock before September" after the season; "+2.8 pts"; Spanish headings in Spanish; readable Today dates; translated "no access" page). 27 new tests prove every money or outside action happens once even after a crash. Demo data can be rebuilt while the worker runs. Agents that plan or review can no longer edit code. | contracts `78d2469`, backend `8ffff2b`, web `d092a4b`, docs `84ec6c6` |
| 21 | Help center (13 articles, English and Spanish) and in-app Help; Terms and Privacy links at sign-up; lawyer-ready drafts (terms, privacy, DPA, sub-processors), incident-response plan, access-control policy; security record corrected (Amazon scans every 30 days); runbook updated. | web `3f383e5`, docs `9a2a88d` |

Gate for wave 20: fresh seed, API golden path 13/13, floor 3/3, full browser run 35/35 (`waves/20/reviews/gate.md`). Owner reports: `waves/20/owner-report.md`, `waves/21/owner-report.md`.

## In progress (built, not yet pushed)
- **Wave 22 (P2 sweep, backend):** contract 0.8.0 is already pushed. USPS end-of-day SCAN forms, carrier address check, rate expiry (re-rate before buying), mailer no longer logs subjects: built (T-22-3), in review. Tenant-safe foreign keys on every table: first half committed; second half (migration lock timeouts, queue stall settings, new shop settings) being finished (T-22-2). Next: production/inventory (QC fail reasons, press maintenance block, bin locations) and orders/vendors (import races, vendor email resend, TikTok 6% fee).
- **Wave 24 (deploy readiness, no AWS):** the AWS configuration is fixed for a first staging deploy (T-24-1, in review). It also fixed things nobody had listed: storage lifecycle rules that matched nothing, storage open to every website, and secrets stored in plain text in task definitions.
- Amazon "$0 shipping" (B-183): not a bug. Amazon's "Unshipped Orders" file has no prices; the "Order Report" does and now has a test. A related real bug was found (re-importing the Unshipped file after the Order Report wipes the totals) and is on the wave 22 orders card.

## Planned and reviewed (not started)
- Wave 23: screens for wave 22's features, floor updates (maintenance block, camera scanner), imaging polish, assistant polish, role/Spanish/offline test suites.
- Wave 24 rest: backend production build and database setup commands, Docker images, and your go-live checklist.
- Wave 25: CI with security scans, E2E in CI, deploy pipeline (written, not run), tracing and alarms.
- Analytics v2 waves A1 and A2 (PM confirmed they fit current scope). A3 waits for your answer on OI-18.

## Blocked on you (safe defaults applied; nothing is waiting idle)
- OI-20: disk nearly full (default: team deletes nothing outside InvAI). Now about 14 GB free.
- OI-19: when to involve a lawyer for the drafts.
- OI-18: which gated analytics parts to build. OI-17: growth items.
- Earlier open items: OI-1, OI-2, OI-3, OI-8 to OI-15.
- New decisions surfaced for later: staging needs real sandbox/test keys for every provider (only a "demo" stage may use mocks); production outbound traffic goes through a single NAT instance unless you choose the managed NAT (a cost choice).

## Next steps
1. Finish wave 22 (two cards), run its gate, push.
2. Finish wave 24 (backend build, Docker, go-live checklist), gate, push.
3. Waves 23 and 25, then analytics A1/A2, then the final report and the roadmap update.
