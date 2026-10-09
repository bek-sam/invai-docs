# Wave 28 plan review: product-manager (2026-10-09)

Verdict: **changes-required** (1 blocking, small; the rest optional). Scope and ordering are sound.

## Scope check
- All five cards carry a valid ref. T-28-1..4 are `always-in-scope: compliance` (scope.md line 17 names Amazon's data-protection rules). T-28-5 is `always-in-scope: bug`. Nothing is outside `scope.md`; no scope-change-request is needed.
- The wave has 5 cards, at most 3 agents at once, no outbound action, no real keys. The wedge (orders, sheets, floor) is not touched, except T-28-5, which protects the import path.
- The B-185..B-188 rows cite the DPP table in `security/v1-review.md` (lines ~130-150), and the table's MFA, lockout, history and 18-month rows match the cards. The anti-virus row still has no backlog id; it is not in this wave and is not a card gap.

## Findings
1. **BLOCKING: grace for newly promoted admins (T-28-2 AC8).** Grace starts at "the later of user creation and the migration". A presser who is promoted to admin or owner months later is blocked on every screen the moment they are promoted, with no warning. Real shops promote staff. Change the grace start to the later of user creation, the migration, and the time the owner/admin role was granted in any org. Add a Given/When/Then for it: a 6-month-old user gets admin today, so the banner shows and nothing is blocked for 7 days.
2. Optional: 7-day grace is the right call for a mid shop with assisted onboarding. A small self-serve shop that signs up gets 7 days to see the banner, which is fine. Keep `MFA_GRACE_DAYS` 0-14 with default 7. Say in decision 0025 that 7 days is a product choice and the owner can change it.
3. Optional: 30-minute lockout after 10 wrong passwords is acceptable. Lockout by guessing is a real nuisance for an owner on a busy day (a competitor or ex-employee can lock the owner's account). Mitigations in the card are enough: the reset link clears the lock (AC2), floor PIN sessions are unaffected, and a single email is sent. Add to AC3 that the lock email says how to unlock now (reset link), not only "locked".
4. Optional: T-28-4 AC1 text says "locked for 30 minutes" but the minutes should come from `retryAfterSec`. Make the sentence use the computed number so the copy never disagrees with the real time left.
5. Optional (owner heads-up, not a blocker): T-28-3 deletes data and cannot be undone. The keep/drop table is a legal call ("legally required" exception, US tax records). Keeping money totals, fees, cost, dates and the order number is the right default for a real shop: profit for a past month must still add up, and sellers keep tax records for years. The card already says keep when unsure and flag for counsel (OI-19). Add one AC: a dry-run mode that only counts what it would clear, and run that first in the exercise, so the owner sees numbers before any real delete. Tell the owner in the wave report that the sweep deletes data and ships dark until deploy.
6. Optional: T-28-3 AC2 limits the sweep to final-state orders. Confirm "refunded" and "returned" exist as states in `invai-contracts/src/states.ts`, or drop the word.
7. Seed/demo (T-28-2 AC12): the seed and golden path stay usable because seeded users are inside their grace. Good. Add a note that the demo owner login will start seeing the banner, and that after 7 days a long-lived dev DB will block the demo owner (`owner@desertbloom.test`) until two-step is on or the seed is rerun. Put this line in `build/demo-guide.md` through the docs-writer, or have the seed set the grace relative to seed time. This could surprise the owner during testing.
8. Optional: T-28-5 exercise edits a seeded connection's setting in the shared dev DB and restores it. Acceptable; add "restore in a `finally`" so a crash does not leave the demo with auto-import off.
9. Acceptance criteria are user-observable for T-28-2, 3, 4, 5 (sign-in refusal, email, error messages, banner, blocked page, orders not imported). T-28-1 criteria are contract-level only, which is fine for a contract card.
10. Process: skipping QA acceptance-tests-first is a recorded deviation under decision 0018; I accept it for this wave given the security reviewer's tests. It must not become the default.

## Backlog diff (30 rows changed)
- 30 status cells changed: 25 closed or partial, 5 planned (B-185..188, B-261). Previous states were all open or partial; none were `done` before.
- Sample checked against the repo: B-166 `WORKER_STALL_SETTINGS` in `lib/queues.ts:53` (found); B-197 `mergeTotals` in `orders/import.ts:413,475` (found); B-162 `printsInHouse`/`shipsSaturday` toggles in `settings/company.tsx:40-41` (found); B-189 guard blocks `sst secret set` and branch-protection API writes (`guard-bash.py:31-32`); B-98 sign-up Terms/Privacy links (`signup.tsx:180-189`); B-105 camera scanner (`CameraScan.tsx`); B-163 `SET LOCAL statement_timeout = 0` (`db/migrate.ts:54`); B-191 `refreshDemand` in the seed (`db/seed/market-demand.ts`). All hold. Nothing wrongly closed. Infra rows are honestly marked "done in config ... verify at the first staging deploy"; keep that wording.

## Needs the owner
- Nothing blocks the plan. Heads-up only: finding 5 (irreversible delete, ships dark) and the 7-day grace and 30-minute lock values (product defaults, changeable by env).

## Commands run
- `ls`, `wc -l`, `cat`/`cut` on `waves/28/wave.md` and T-28-1..5
- `grep -n -i -A12 "always in scope" product/scope.md`; `sed -n 120,160p security/v1-review.md`
- `git -C invai-docs diff --stat -- waves/backlog.md`; `git diff -U0 -- waves/backlog.md | grep '^+|'` (and the `-` side, counted by old status)
- `grep -n` for the 8 evidence items above in `invai-backend/src`, `invai-web/src`, `invai-floor/src`, `.claude/hooks/guard-bash.py`
