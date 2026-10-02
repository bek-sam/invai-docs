# Wave P3 — the floor rate-limit fix, one gate, push P1 + P2 + P3

**Dates:** 2026-10-01.

## What was built
- **T-P3-1** Rate-limit buckets by intent (B-236) (backend-foundation) — the actual fix:
  reads and writes now draw from separate rate-limit buckets.
- **T-P3-2** Floor shows 429 as busy; fewer signed URLs (B-237) (floor-engineer) — the
  user-facing half: a rate-limited floor tablet says "busy," not "offline."
- **T-P3-3** es money: thousands separator on 4-digit amounts (product-designer).
- **T-P3-4** Losing orders Units 0 / Revenue $0 (B-230, verify first) (backend-engineer/
  analytics) — closed with no product change once root-caused to a different bug
  (B-242, fixed properly in wave P4).
- **T-P3-5** Market tests stop leaking cache rows (B-221) (backend-engineer/market) —
  approved only as a partial fix; the rest moved to P4.

## Why
This wave's goal names the exact user-visible failure: "a busy floor never gets a scan
rejected because thumbnail reads used up the shop's write allowance; if the server does
say 'slow down,' the presser sees 'busy,' not 'offline.'" A presser who sees "offline" on
a working tablet will stop trusting it.

## What went wrong
- The actual root cause took real digging: a floor scan got HTTP 429 because thumbnail
  *reads*, sent as POST requests, were sharing the same rate-limit bucket as writes — and
  the floor client mapped every retryable status, including 429, to its offline path. Two
  earlier gates had already blamed this on a timeout or job contention before a
  Playwright trace's network log finally showed the real status code.
- Two builders (T-P3-4 and T-P3-5) ended their turns while their own background test runs
  kept going, with no report — one of them (T-P3-4/T-P3-5) was stopped and relaunched
  four times as a result, and the orphaned runs competed for RAM with everything else on
  the machine.
- The machine itself hit about 15 of 16 GB RAM with swapping, because a gate run, a
  reviewer's full suite and a builder's full suite all ran at the same time — two full
  backend runs died, and a gate run failed at test start-up.
- An agent reported a file revert as "done" when the guard hook had actually blocked it —
  `git status` still showed the file modified, and the tech lead had acted on the report
  without checking first.

## What the team learned
- Root-cause an E2E failure from the Playwright trace's network log (actual status codes)
  *before* forming a load or timing hypothesis — now a named step in `run-golden-path`.
- Run tests in the foreground and never end a turn while a test run you started is still
  going — now in `verify-and-report` step 5.
- At most 2 heavy test runs (full suite, gate, E2E) on the machine at once.
- After any agent claims a file change, check `git status` or `git log` before relying on
  the claim — reports are self-described, not verified by default.

## Files to look at
- `invai-backend/src/lib/rate-limit.ts` — intent-based buckets (T-P3-1).
- `invai-floor/src/api/rpc.ts` (429 handling) — "busy," not "offline" (T-P3-2).
- `invai-ui/src/lib/format.ts` — es money grouping (T-P3-3).
- `invai-backend/src/modules/analytics/service.ts` — where B-230 was ruled "not this bug" (T-P3-4).
- `invai-docs/team/lessons.md` (2026-10-01, "wave P2 gate", "wave P3" rows — four of them).
