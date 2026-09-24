# Review of T-1-4 (round 2)

- Reviewer: reviewer on Opus
- Author: backend-foundation on Opus 5.5
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend diff --stat 659f1bc^ 659f1bc` | 7 files, all in `modules/tenancy/` and `modules/vendors/` — matches the card's owned paths and the tech lead's message. Web unchanged (`d6336e0` still stands, confirmed no new web commit). |
| Clean worktree at `659f1bc` (`git worktree add --detach`, `node_modules` **symlinked**, no `pnpm install`, own test DB `invai_test_r14b`) | set up as instructed |
| `./node_modules/.bin/tsc --noEmit` | clean |
| `./node_modules/.bin/biome check .` | "Checked 197 files… No fixes applied." |
| `./node_modules/.bin/vitest run --passWithNoTests` (`TEST_DATABASE_URL=postgres://invai_app:invai@localhost:5432/invai_test_r14b`) | `Test Files 39 passed (39) / Tests 231 passed (231)` |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend 659f1bc^` | **exit 0, no hits** (0 assertions removed, 11 added; the wrong base `55ca092` pulls in two unrelated cards' commits and false-positives on T-1-3's supplier-adapter mocks — `659f1bc^` is the correct base for isolating this commit) |
| **Mutation test (my own, not the author's):** reintroduced the round-1 bug by wrapping the `sendInviteEmail` call in `inviteTeammate` back inside a `withTenant(...)`, reran `invites.test.ts` | both new tests fail exactly as expected: `expected [{ busy: 1, committed: true }] to deeply equal [{ busy: 0, committed: true }]` on "sends the email after the invitation is committed, with no transaction open" and on "removes the committed invitation when the email fails, and keeps an older link working". Reverted; `git diff` clean; reran — 231/231 pass again. |
| Live: API on `PORT=3195` against a throwaway copy of the dev DB (`createdb -T invai invai_r14b_copy`) | see below |
| Owner invites `r14b.retry@` as `office` (mail up) → restart API with `SMTP_URL=smtp://localhost:1` (nothing listening) → re-invite same email as `presser` (role change attempt) | second call: `502 UPSTREAM_FAILED`. `select id,email,role,status from invitations` shows **only the original row, `role: office`, `status: pending`** — the old invitation and its link are untouched and still `invite-preview`-able. No second row (pending or canceled) left behind — the failed attempt's row is fully deleted. |
| Fresh (non-re-invite) staff invite with mail down; fresh vendor invite with mail down | both `502 UPSTREAM_FAILED`; `select count(*) from invitations`, `companies` (vendor org), `vendor_connections` for those emails/names all `0` |
| `select state, count(*) from pg_stat_activity where datname='invai_r14b_copy'` after all of the above | only `idle`, never `idle in transaction` |
| Cleanup | dropped `invai_r14b_copy`/`invai_test_r14b`, removed the worktree, stopped the API, port 3195 free |

## What I was asked to check
1. **No-open-transaction tests.** Real and load-bearing — see the mutation test above; they fail immediately and specifically when the bug is reintroduced, not just on unrelated breakage.
2. **Compensation on failure.** Verified in code and live: a failed staff invite deletes only the just-inserted invitation (`inviteTeammate`'s catch block, `tx.delete(invitations).where(eq(invitations.id, invitation.id))`); a failed vendor invite deletes only the vendor org **it created** (`removeNewOrg`, gated on `invitation` being set, so an already-existing vendor org is never touched — confirmed by reading `inviteVendor`: `invitation` stays `null` when `existingOrg` is truthy). The vendor path's final write step also re-checks `assertNotConnected` before inserting and compensates if a concurrent request won the race first — a real, not theoretical, guard against orphaning a vendor org.
3. **Behavior change: a failed re-invite leaves the old link valid.** Confirmed true, live and in the new unit test ("removes the committed invitation when the email fails, and keeps an older link working"). This is a deliberate, disclosed tradeoff, and it's the right one: the alternative (cancel-then-send, as round 1 effectively also produced whenever the whole transaction rolled back on failure) risks destroying a working invitation for no benefit when the replacement never went out. Not blocking. One note for a follow-up, not this card: the error toast ("The invite email didn't go out…") doesn't tell the owner that an older invitation for that person is still active with its original role — worth a copy tweak so an owner trying to *downgrade* a mis-invited role via re-invite doesn't wrongly assume nothing is pending. Flagging for product-designer/tech lead, not blocking here.
4. **The late-delivery window after the 15 s timeout.** `deliverInviteMail` races `sendMail` against a 15 s timer with `Promise.race`; this correctly turns a hang into `UPSTREAM_FAILED` (proven directly by the new unit test with a 500 ms mock delay and a 50 ms timeout) and doesn't leak a listener (the `finally` clears the timer). It does **not** abort the underlying SMTP call — a send that completes after the 15 s mark can still deliver a real email whose invitation has already been deleted by the compensation step, landing the recipient on "This invite link doesn't work." The author discloses this explicitly as a known gap and it doesn't regress anything: worst case is a rare dead link after an error the inviter already saw, not a security or data issue, and 15 s is generous for both Mailpit and typical SMTP relays. Non-blocking. (I tried to reproduce the actual 15 s-timeout path live with a `nc`-based hanging listener; `nc` on this box closes the socket immediately rather than truly hanging, so that attempt just re-proved the fast-failure path. The unit test with a controllable mock delay is the correct way to prove this and it does.)

## Blocking findings
None. Round 1's finding is resolved and independently verified past the author's own claims (mutation test, live re-invite-under-outage test, live fresh-invite test, live vendor test, connection-state check).

## Checks
- [x] Only owned paths changed (7 files, `modules/tenancy/**`, `modules/vendors/**`).
- [x] Nothing outside scope; web untouched.
- [x] Tests exercise the behavior, none weakened (`scan-test-weakening.sh` clean on the correct base; I also mutation-tested the two key assertions myself).
- [x] Tenancy/idempotency — the mail send is now outside every transaction (proven); compensation is scoped correctly per path; the vendor path is race-safe against a concurrent duplicate connect. See optional note below on a latent, pre-existing double-submit gap this round didn't introduce.
- [x] Decisions recorded — round 2 section of the report documents the compensating-transaction design, the `afterCommit`-can't-report-failure reasoning, and both known gaps (timeout race, partial-failure-after-send).

## Optional notes (not blocking)
- `invitations` has no unique index on `(organization_id, lower(email))` for `status = 'pending'`. Two near-simultaneous identical `team.invite` calls (a double-click) can each pass the "no existing member" check before either commits, sending two invite emails; the later "finish" step to cancel older pending invitations resolves it down to one live invitation, but the duplicate email still goes out. Pre-existing since round 1 (no constraint was added there either), not introduced by this diff, and low impact (one extra email, no double member creation since accept-invitation is per-invitation-id). Worth a follow-up card, not a blocker.
- Same UX note as above, restated: consider surfacing "an earlier invitation for this person is still pending as <role>" in the failure toast.
