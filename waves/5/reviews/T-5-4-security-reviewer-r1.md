# Review of T-5-4 (round 1) — security co-review

- Reviewer: security-reviewer on Sonnet 5
- Author: web-engineer + backend-foundation on Opus 5.5
- Verdict: changes-required

Scope: the `auth` risk flag — PIN-only placeholder email, invite/resend/revoke state transitions,
role escalation. Ownership/style/UI/UX are the primary reviewer's and product-designer's files.

Co-review under the card's `auth` risk flag (`threat-model-change`). Entry points: `team.invite`
(now accepts `pinOnly`), `team.resend`, `team.revoke` (both new), `stations.revokeToken` (existing,
exercised here). All are `proc("team.manage"|"stations.manage")`, session-derived tenant, Zod-validated
input — no new webhook, file or payment surface.

## Evidence I re-ran
| Command | Result |
|---|---|
| `grep -n "withSystem(" invai-backend/src/modules/tenancy/service.ts` | none in the touched functions — `addPinOnlyStaff`, `inviteUser`, `resendInvitation`, `resendInvite`, `revokeInvite` all run under `withTenant` |
| `grep -n "permission:" invai-contracts/src/contract/tenancy.ts` around `resend`/`revoke` | both `proc("team.manage")` — same permission as `invite`/`changeRole`; no new permission introduced, no weaker one used |
| `pnpm test src/api/authz.test.ts` (backend main tree) | passing (part of the 480/67 files re-run in the reviewer file) — generic per-procedure permission sweep, no new gap needed since `resend`/`revoke` reuse `team.manage` |
| Live: `pin+<uuid>@floor.invai.internal` via `POST /api/auth/sign-in/email` | 401, no session cookie (reviewer file, AC1) |
| Live: `POST /team/invite {email: <the placeholder>, ...}` (as a second admin trying to invite the placeholder as a "real" address) | `400 BAD_REQUEST "That address can't receive email"` (`inviteUser`, `service.ts:344`) |
| `pin-only.test.ts` "the placeholder is never mailed or invited" (re-run) | passing — `sendMail({to: placeholder})` returns `{messageId:"skipped:pin-only"}` |
| `grep -n "sendAuthMail" invai-backend/src/auth.ts src/lib/auth-mail.ts` | `sendResetPassword` and `sendVerificationEmail` both call `sendAuthMail` → `sendMail` (`mailer.ts`), the same function `isPlaceholderEmail` guards — reset/verify mail for a `pinOnly` address is a no-op the same way invite mail is |
| Read `db/schema/tenancy.ts` diff + `drizzle/0018_team_pin_only_invites.sql` | `pin_only` boolean NOT NULL DEFAULT false on `users` (Better-Auth-owned table, no RLS by design, same as every other `users` column); `invitations_pending_org_email_unique` is a **partial** unique index (`WHERE status='pending'`) on `(organization_id, email)` — correctly tenant-scoped (keyed by `organization_id`, not by email alone), so a pending invite in company A never blocks the same email in company B |
| `changeRole` PIN-only guard (`service.ts:515-521`) re-read | blocks moving a `pinOnly` user to any non-floor role — closes the obvious escalation ("invite as packer, then promote to owner and the placeholder is now the login for an owner-equivalent web account") before it can happen; `addPinOnlyStaff` itself refuses non-floor roles at creation too |

## Threats walked (10 threats, InvAI cases)
| # | Threat | This change | Control | Gap |
|---|---|---|---|---|
| 1 | Cross-tenant read/write | invite/resend/revoke by another company's invitation id | `pendingInvitation`/`getMember` filter by `organizationId` inside `withTenant`; `NOT_INVITED`/`NOT_FOUND`, never a row from another tenant | none found |
| 2 | Privilege escalation | PIN-only member promoted off the floor, or invited straight to owner via `pinOnly` | `addPinOnlyStaff` refuses non-floor roles; `changeRole` refuses moving a `pinOnly` user off a floor role; `pinOnly` invites also route through `assertRoleFitsOrg`/`assertCanManage` like any invite | none found |
| 3 | Spoofed/replayed action | double-revoke, double-resend | revoke: second call is `409 NOT_INVITED` (verified live), not a silent no-op that could mask a race; resend: reuses the same invitation id and re-sends, no duplicate row | none found |
| 4 | Foreign id from input | `userId` on resend/revoke is actually an invitation id read cross-tenant | scoped by `organizationId` (see #1) | none found |
| 5 | PII leak | placeholder email rendered/logged as if real | web never renders `email` when `pinOnly` (shows "PIN only, no email"); backend logs `mail skipped: PIN-only placeholder address` with **no address**, only the subject (`mailer.ts`) | none found |
| 6 | Injection / domain collision | could `floor.invai.internal` collide with a real, attacker-controlled mailbox, or be guessed and used to trigger a mail/reset flow | `.internal` is an IETF-reserved special-use TLD (RFC 9476), never delegatable in public DNS, so no real mailbox can ever answer to `*.floor.invai.internal`; the local part is a fresh `randomUUID()`, not derivable from the user's name/role, so it isn't guessable either | none found |
| 7 | n/a (no AI/prompt surface in this change) | | | n/a |
| 8 | Abuse without limits | unbounded resend spam to one invitee | `resend` still goes through `team.manage` (an authenticated admin/owner has to be the one spamming, same as re-inviting today); no new rate limit added, but the blast radius is "your own admin annoys your own invitee," not external abuse | not a gap worth blocking on |
| 9 | Fail-open | mailer/DB errors during invite/resend | `inviteTeammate`/`resendInvitation` send mail *then* commit the row change; a failed send leaves the prior state untouched and raises, so the failure mode is fail-closed (no state change without proof of send) | none found |
| 10 | Double side effect | invite race (two concurrent invites for one email) | partial unique index + `23505`→`CONFLICT` catch — verified in code and by `invites.test.ts`'s "the database allows one pending invite per company and email" | **see below**: the symmetric case, revoke racing accept, is not guarded the same way |

## Blocking findings
1. Same underlying defect as the primary reviewer's finding 1 (`invai-backend/src/modules/tenancy/service.ts:434-439`): `revokeInvite`'s `UPDATE` lacks a `WHERE status = 'pending'` guard. From a threat-model angle this is threat #10 (double/conflicting side effect) rather than a tenancy or auth-bypass issue — it cannot grant access (the `members` row from a genuine `acceptInvitation` is untouched), but it can make the `invitations` audit trail assert something false ("revoked" on a row that was actually accepted), which is a real problem for an audit-driven investigation ("who let this person in, and when") after an incident. Given the card's `auth` risk flag exists specifically so invite/accept/revoke state transitions are trustworthy, I'm joining the primary reviewer's `changes-required` on this rather than downgrading it to a note. Severity: **Low** (no cross-tenant or escalation blast radius, single-tenant audit-integrity issue only) — does not need owner sign-off to accept as a finding, but should be fixed before push per the "revoke racing accept" item the card explicitly calls out.

## Checks
- [x] Tenancy (`withTenant`, RLS on new tables) — no new tenant table; `users.pin_only` and the
  partial unique index are on Better-Auth-owned tables scoped by `organization_id`/company id
  explicitly in every query touched; no new `withSystem` in the diff
- [x] Idempotency — invite/resend/revoke all safe to retry, except finding 1 (revoke racing accept)
- [x] No PII leak — placeholder email never logged, never rendered, mail silently skipped
- [ ] Invite/revoke state transitions are race-safe — revoke is not (finding 1)
- [x] No privilege escalation path found (PIN-only stays floor-role in both directions)

## Worst outcome
If finding 1 is left as-is: an admin's revoke click that loses a race with a genuine accept produces a false "revoked" audit entry for a user who is, in fact, an active team member with real permissions — an investigator reading the audit log after an incident could wrongly conclude that person was never granted access. No unauthorized data access or privilege change results from the race itself.

## Decisions and follow-ups
- Required before merge: the `WHERE status='pending'` guard on `revokeInvite`'s update (finding 1 above / reviewer finding 1).
- Accepted risk: none needed — no High findings.
- New finding ids in `security/v1-review.md`: none filed; this is scoped as a review blocking finding on an unpushed card, not a finding against already-shipped code.
