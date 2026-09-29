# Review of T-21-3 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: security-reviewer on Sonnet 5
- Verdict: changes-required

Scope reviewed: invai-docs commit `ed0ef87` (security/v1-review.md, new security/vulnerability-management.md, waves/21/reports/T-21-3.md). Docs-only card.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-docs show --stat ed0ef87` | `security/v1-review.md` (+37/-14), `security/vulnerability-management.md` (+70), `waves/21/reports/T-21-3.md` (+48). Owned paths plus the report only. |
| `grep -rn 180 invai-docs/security` | no output, rc=1 (AC1 verification passes) |
| `grep -rn -i "every 180\|180 days" invai-docs .claude/agents` | Still says 180 days: `invai-docs/architecture.md:435` and `research/04-apis-and-ai-feasibility.md:99`. Both are outside `security/**` (not blocking, see notes). |
| S-15: `sed -n 173,209p` and `333,340p invai-backend/src/auth.ts`; `ls src/api/email-gate.test.ts`; `ls waves/2/T-2-3-*` | `requireEmailVerification: false` with the cited comment (175), `emailVerification.sendOnSignUp: true` (195-209), accept-invite marks verified (333-340), gate test exists, T-2-3 card exists. Invites are now real emailed invitations (`tenancy/service.ts` inviteTeammate, no more member-by-email attach), so the original takeover path is closed. **Fixed: confirmed.** |
| S-28: `sed -n 18,30p` and `70,100p invai-backend/src/api/webhooks.ts`; `git log -- src/api/webhooks.ts` | Verify on the raw body, then 401 (75-80), then the delivery id, then `webhook_deliveries`, then enqueue. Landed in `90657ac` (T-1-2). **Fixed: confirmed.** The row cites file:line, not the commit (acceptable under AC4). |
| S-31: `sed -n 118,127p invai-backend/src/modules/files/service.ts`; `grep -n "SVG is always forced" service.test.ts`; `git log -S forceAttachment` | `forceAttachment` for `image/svg+xml` (122-124), test at line 111, commit `7411508` (T-12-5). **Fixed: confirmed.** |
| S-30: `sed -n 100,126p src/api/app.ts`; `src/api/health.test.ts:6-10`; `events.ts:20-24`; `context.ts:88-94`; `env.ts:227` | `/health` returns booleans only, and the test asserts no `/mock/i`. The SSE `?token=` is still accepted, `clientIp` has no trusted-proxy list, and `FLOOR_TOKEN_SECRET` still falls back. **Partially fixed: confirmed.** |
| Still-open spot check, S-29 and S-14 | S-29 "Open (accepted for v1)" is unchanged, consistent with the report. S-14 "Mitigated": `app.ts:169-170` still mounts `noMockWebhooksInProd`. Consistent. |
| Status tally: python over every `\| S-NN` row of v1-review.md, severity + status cell | High 6/6 fixed. Medium 16: 15 fixed, S-14 mitigated. **Low 15: 9 fixed (S-20..S-25, S-27, S-28, S-31), S-34 closed, S-30/S-37 partial, 3 open (S-26, S-29, S-32).** |
| `grep -n` backlog for each "Open, no backlog id yet" DPP row | `B-75` "Alarms, SNS, budget, 12-month log retention" open (wave 25); `B-23` "KMS field encryption ... 18-month retention", KMS part open (wave 24); `B-74` "RDS production settings (size, backups, ...)" open (wave 24). |
| `grep -n -i "18 month" invai-backend/src` | `modules/privacy/service.ts:761` and `privacy/jobs.ts:63`: a daily job already removes buyer PII from orders older than 18 months. |
| `sed -n 378,381p src/auth.ts`; `sed -n 58p invai-infra/sst.config.ts` | twoFactor plugin (optional) and the unused KMS key: both citations correct. |
| `grep -n "B-08\|B-21" waves/backlog.md`; `grep -n T-25-1 waves/25/wave.md`; `grep -n T-22-2 waves/22/wave.md` | B-08 and B-21 open (wave 25); T-25-1 and T-22-2 planned. Pointers correct. |
| `.claude/skills/dependency-and-container-audit/SKILL.md` lines 3, 12, 74 | 30-day cadence and the 7/30 clocks match vulnerability-management.md. |
| Amazon source URLs | Not re-fetched (no web tool in this review session). The quotes match research 12 line 11 and its correction 1, which cite the same vulnerability-management URL. Access date is given. Accepted on that cross-check, not on a fresh fetch. |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-docs origin/main` | No test changes in this commit. |

No processes started. Shared dev DB untouched.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | `grep 180` is empty. Item 5 and vulnerability-management.md state 30-day scans, a code scan before release and a 365-day pen test with retest, with the URL and access date 2026-09-28. |
| 2 | Partly | The 12-row DPP table exists with InvAI's state for each change. **Gap column is wrong for 3 rows** (finding 1). |
| 3 | Yes | Cadence, owner (`dependency-and-container-audit`), SLAs 7/30/90 (Medium labeled as InvAI policy), owner-inbox exception process, evidence locations, and "planned: wave 11 prep" plus T-25-1, B-08 and B-21. |
| 4 | Partly | S-15, S-28, S-30 and S-31 status changes are correct, each with file:line (checked above). **The summary count line contradicts the table** (finding 2). |

## Blocking findings
1. `security/v1-review.md:121` (log retention), `:122` (TLS/KMS), `:125` (geo-dispersed backups): Gap says "Open, no backlog id yet", but backlog rows exist: B-75 (12-month log retention, wave 25), B-23 (KMS field encryption, wave 24) and B-74 (RDS backups, wave 24). AC2 requires the backlog id when one exists. The 18-month row (`:120`) also leaves out B-23 and the existing 18-month buyer-PII job (`privacy/service.ts:761`); the DPP non-PII gap is still real, but the row should say what exists. Failure: the report routes these to the tech lead as "needs a backlog row". That creates duplicate B-rows for work already planned in waves 24/25, and the evidence pack shows tracked work as untracked. Fix: cite B-75/B-23/B-74 in those cells, and remove them from the "no backlog id" list in the report.
2. `security/v1-review.md:49` counts line ("Counts as of 2026-09-28 ... 8 fixed, ... 4 open: S-25, S-26, S-29, S-32"): S-25's own row says "Fixed" (line 35), and the "What remains open" list correctly leaves it out. The correct Low tally is 9 fixed, 1 closed, 2 partially fixed, 3 open (S-26, S-29, S-32). AC4 is "the findings table is current", and the report quotes this line as the corrected count. Failure: the SP-API evidence pack takes the summary line and reports four open findings, one of them already fixed. Fix: correct the line.

## Checks
- [x] Only owned paths changed (`git diff --stat`): `security/**` plus the card's report.
- [x] Nothing outside scope. The author correctly didn't edit backlog, architecture.md or create evidence folders.
- [x] Tests: none; scan clean.
- [x] Tenancy, idempotency, cents, en/es: not applicable (docs).
- [x] Decisions recorded where needed: the Medium 90-day SLA is stated as InvAI policy in the doc, which is enough for now. It is a candidate for a security decision record if other docs start citing it.

## Optional notes (not blocking)
- `invai-docs/architecture.md:435` and `research/04-apis-and-ai-feasibility.md:99` still say "at least every 180 days". They are outside this card's paths. The tech lead should route them to the architect / research owner (research 12 G31 also names "the security-reviewer role" file; `.claude/agents/security-reviewer.md` has no 180, so that part is done).
- DPP row "TLS terminates at the ALB (infra)" has no citation; point it at `sst.config.ts` or mark it planned.
- The commit message says S-15/S-28/S-31 were fixed in "wave 2/T-19". S-28 was actually T-1-2 (`90657ac`) and S-31 was T-12-5 (`7411508`). The doc itself is right; you could add the commit ids to the S-28 row for AC4 symmetry.
- vulnerability-management.md "CI jobs" is one very long paragraph; a short list would read better.
