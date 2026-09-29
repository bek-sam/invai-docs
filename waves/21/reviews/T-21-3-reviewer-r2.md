# Review of T-21-3 (round 2)

- Reviewer: reviewer on Sonnet 5
- Author: security-reviewer on Sonnet 5
- Verdict: approve

Scope reviewed: invai-docs commit `6fc90a2` (`security/v1-review.md`, `waves/21/reports/T-21-3.md`,
"Round 2" section). Verified both round-1 blocking findings against the sources the fix cites, cold.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-docs show --stat 6fc90a2` | `security/v1-review.md` (+9/-9), `waves/21/reports/T-21-3.md` (+15). Owned paths plus the report only. |
| `git -C invai-docs diff --stat origin/main -- security/ waves/21/reports/T-21-3.md` (cumulative r1+r2) | Same two files (plus the new `vulnerability-management.md` from round 1). Nothing outside `security-reviewer`'s owned paths. |
| Finding 1 (DPP table backlog citations): `grep -n "B-75\b\|B-23\b\|B-74\b\|B-185\|B-186\|B-187\|B-188" invai-docs/waves/backlog.md` | B-75 (log retention, platform-sre, wave 25, open), B-23 (KMS field encryption, backend-foundation + security-reviewer, "KMS field encryption open (wave 24)"), B-74 (RDS backups incl. geo-dispersed, platform-sre + backend-foundation, wave 24, open), B-185 (account lockout, "wave 21 T-21-3", open, before SP-API application), B-186 (password history), B-187 (18-month non-PII retention sweep), B-188 (mandatory owner/admin MFA) — all present and all cited correctly in the fixed table rows. |
| `sed -n '755,765p' invai-backend/src/modules/privacy/service.ts`; `grep -n "18" invai-backend/src/modules/privacy/jobs.ts` | The 18-month non-PII row's new text ("A separate daily job already removes buyer PII from orders older than 18 months... done under B-23/T-12-4. That job covers buyer PII, not non-PII order payloads") — `service.ts:761` is inside the 18-month purge logic and `jobs.ts:63` schedules it daily. The row's own gap statement (no sweep for non-PII beyond the buyer-PII purge) is unchanged and still accurate; it now correctly acknowledges what exists first. |
| Finding 2 (Low count line): re-tallied every `S-2\|S-3` row's Status cell in `v1-review.md` by hand | Fixed: S-20, S-21, S-22, S-23, S-24, S-25, S-27, S-28, S-31 (9). Closed: S-34 (1). Partially fixed: S-30, S-37 (2). Open: S-26, S-29, S-32 (3). 9+1+2+3=15, matches the stated Low total of 15. The new count line text matches this tally exactly, including naming S-25 among the fixed (its own row at line 35 says "Fixed", confirming it does not belong in "open"). |
| `grep -n "no backlog id yet" invai-docs/security/v1-review.md` | One remaining hit: the anti-virus/malware-disablement row, which genuinely has no backlog id and is correctly left as-is (not overclaimed). |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-docs origin/main` | No test files changed by this commit. |

No processes started. Shared dev DB untouched.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes (unchanged from round 1; not touched this round) | — |
| 2 | Yes | Every DPP table row that had a real backlog id now cites it (B-75, B-23, B-74) and every genuinely-new gap now has a freshly filed id (B-185-188), each present in `waves/backlog.md` with the right owner and "wave 21 T-21-3" source. Only the anti-virus row is left without an id, correctly, since none exists. |
| 3 | Yes (unchanged from round 1) | — |
| 4 | Yes | The Low-severity count line now matches a hand re-tally of every row's Status cell (9 fixed / 1 closed / 2 partial / 3 open = 15). |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat`): `security/v1-review.md` plus the card's own report.
- [x] Nothing outside scope: the four new backlog rows (B-185-188) were added by the tech lead per the report, not by this author — correctly not claimed as this author's own edit to `waves/backlog.md` (which isn't in this card's owned paths).
- [x] N/A — docs-only card, no tests to weaken; scan-test-weakening clean.
- [x] Tenancy/idempotency/cents/en-es: not applicable (docs).
- [x] Decisions recorded where needed: none needed; citing existing/new backlog ids in a findings table isn't a decision-record-level change.

## Optional notes (not blocking)
- The 18-month non-PII row is now noticeably long (three clauses: what exists for PII, what's missing for non-PII, the backlog id). Readable, but a future pass could split "what InvAI does today" into two sentences for scannability. Not worth a third round.
