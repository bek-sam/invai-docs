# Wave 28: Amazon data-protection hardening, one import bug, and a true backlog

- Dates: 2026-10-09 →
- Goal (user outcome): before the Amazon SP-API application, every owner and admin account is protected the way Amazon's Data Protection Policy asks (account lockout after 10 wrong passwords, no reuse of the last 10 passwords, two-step sign-in required for owners and admins, Amazon order data older than 18 months cleared except bookkeeping records); a shop that turns auto-import off gets no more polled imports (webhook imports are a PM question, B-292); and the backlog's open count is honest.
- Owner order 2026-10-09: "push everything to 100%, go". This tech lead runs only wave 28.
- Scope ref: always in scope (compliance: Amazon DPP 2025-11-25, `security/v1-review.md`; bug: B-261).
- Fences: no deploys, no real keys, no outbound sends; gates run with AI keys blanked. Owner-pending items not touched: OI-3, OI-8, OI-13, OI-17, OI-21, OI-25. At most 3 agents at once, reviewers included. No canary planted (OI-15 still open).
- Plan reviewed by: product-manager (2026-10-09, changes-required, 1 blocking: grace restarts on promotion) and architect (2026-10-09, changes-required, 8 blocking card-text edits: vendor role, one per-user rule, sample orgs, email-keyed lockout, `MFA_DISABLE_NOT_ALLOWED` and auth codes in the contract, owned-path gaps, no "refunded" state, sweep loop predicate). All were edits to card text with exact wording supplied, applied as written; no redesign, so no second plan round (`reviews/plan-pm.md`, `reviews/plan-architect.md`).

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| [T-28-1](T-28-1-mfa-contract.md) Contract: `MFA_REQUIRED` common error, optional `Me.mfa`, `AUTH_ERROR_CODES` + `AccountLockedBody` | architect | sonnet | reviewer (opus) + backend-foundation (sonnet) + web-engineer (sonnet) | auth, contract | planned |
| [T-28-2](T-28-2-account-security-backend.md) Backend: per-account lockout (B-185), password history (B-186), required two-step sign-in for owner/admin with a 7-day grace (B-188) | backend-foundation | opus | reviewer (fable) + security-reviewer (opus) | auth, migration | planned |
| [T-28-3](T-28-3-amazon-retention-sweep.md) Backend: 18-month sweep of non-PII Amazon order data, bookkeeping records kept (B-187) | backend-engineer (privacy) | opus | reviewer (fable) + security-reviewer (opus) + compliance-officer (sonnet) | pii, tenancy, data deletion | planned |
| [T-28-4](T-28-4-account-security-web.md) Web: lockout and reuse messages, two-step banner and required-setup page (B-188 web) | web-engineer | sonnet | reviewer (opus) + security-reviewer (sonnet) | auth, ui | planned |
| [T-28-5](T-28-5-skip-poll-sync-when-auto-import-off.md) Channels: skip poll-started syncs when auto-import is off (B-261) | backend-engineer (channels) | sonnet | reviewer (opus) | none (import area, gate covers it) | planned |

## Order and slots (3 agents at once)
1. Plan review: product-manager and architect in parallel.
2. Build slot A: T-28-1 (short; commits the contract first), T-28-2, T-28-5. When T-28-1 or T-28-5 finishes, its reviews and T-28-3 take the free slots.
3. T-28-4 after T-28-1 and T-28-2 are committed (it needs the backend running).
4. Reviews as each card finishes; the gate when every card is approved.
- Ports: T-28-2 API 3121, T-28-3 none (scripts on `invai_test`/scratch), T-28-5 API 3151, T-28-4 the :3000/:5173 slot. Valkey DBs for scratch work: 12 (T-28-2), 13 (T-28-3).

## Agreed interfaces
- Contract (T-28-1): `COMMON_ERRORS.MFA_REQUIRED` = 403, `data: { deadline: Timestamp | null }`; `Me.mfa?: { required: boolean, enabled: boolean, deadline: Timestamp | null }`.
- Better Auth errors (T-28-2 provides, T-28-4 maps; contract constants `AUTH_ERROR_CODES` and `AccountLockedBody`): `ACCOUNT_LOCKED` (423, `retryAfterSec`) on sign-in; `PASSWORD_REUSED` (400) on change/reset password; `MFA_DISABLE_NOT_ALLOWED` (403) when a required user tries to turn two-step off.
- Required = an active owner/admin membership in any non-sample org, per user (vendors, whose only role is `vendor`, are excluded). `MFA_EXEMPT_PROCEDURES = {me.get, me.switchOrg}`.
- Values: lockout 10 wrong passwords per normalized email (HMAC-keyed; unknown emails lock too) → 30 minutes; history last 10; grace `MFA_GRACE_DAYS` default 7 (0–14) from `users.mfa_grace_starts_at` (default now(), restarted when a user becomes required). Decision 0025 (T-28-2, security, proposed).
- `sweepStaleAmazonData(now, {dryRun})` in `modules/privacy/service.ts`, called by the existing daily `privacy.retentionSweep` after the PII sweep; the module's 18-month cutoff on `placedAt`; final-state (shipped, delivered, cancelled) Amazon orders that still hold drop data; keep/drop table in decision 0026 (T-28-3, proposed; compliance and security accept).

## Process notes
- **Backlog reconciliation** (owner candidate 1) is tech-lead curation of a file the tech lead owns, so it ran as planning work, not a card: a read-only sonnet helper gathered evidence, the tech lead edited 30 rows (25 marked done or partial with evidence, 5 planned for this wave). The PM checks it in the plan review. Counts after: 160 done, 88 open, 22 proposed, 10 partial, 5 planned (wave 28), 2 blocked, plus 4 other (291 rows). Before: 137 done, 112 open.
- **QA acceptance tests first** are skipped this wave (decision 0018 token budget; three of five cards are security-reviewed and the security reviewer proves issues with failing tests; the gate runs every suite). Recorded as a deviation.

## Integration gate
- [ ] Fresh reset, migrate, seed, AI keys blanked
- [ ] `run-golden-path` passes (API, browser, floor)
- [ ] Key screens: not looked at by agents (decision 0024); the owner checks them from the feature test guide
- [ ] Pushed to `main` (commits: …)

## Team metrics
| First-pass approvals | Canary caught? | Escaped defects | Reopened | Avg cycle time | Tokens per card |
|---|---|---|---|---|---|

## Log
- 2026-10-09 Fresh tech lead. State: all repos clean and pushed (contracts 9026680, backend 6bf766e, web 0495189, floor 9304da1, ui 52af2b8, imaging f2d2eda, infra 1644dd4, docs acf2493); no app process listening on 3000–3199, 5173, 5174, 8000; 31 GB free. Backlog reconciled; cards written; plan review started.
- 2026-10-09 Plan reviews applied (docs 36be8af). B-292 added (webhook imports while auto-import is off, PM decision). Builders started: T-28-1 (architect, sonnet), T-28-2 (backend-foundation, opus, API 3121), T-28-5 (backend-engineer, sonnet, API 3151).
- 2026-10-09 T-28-1 built (contracts dc62328, 0.13.0; 146 tests; backend and web typecheck clean). Its reviews wait for a slot; T-28-3 (backend-engineer privacy, opus) started in the free slot.
- 2026-10-09 T-28-5 built (backend 8dcb068, d5e8fd1; 4 new tests; full suite 1644 pass; real run: poll skipped, manual sync imported 1 mock order into the dev DB, settings restored). One reviewer (opus) reviews T-28-1 and T-28-5, one file each.
- 2026-10-09 Reviewer r1 approve on both (T-28-5 tests proven to fail on origin/main). **T-28-5 approved.** T-28-1 waits for its consumer co-reviews (web-engineer started; backend-foundation next).
- 2026-10-09 T-28-1 web-engineer r1 approve, backend-foundation r1 approve: **T-28-1 approved.** Notes for T-28-2/T-28-4 reviews: assert the 423 body with `AccountLockedBody.safeParse`; `deadline` ISO with offset; web falls back to `Retry-After`, `shouldRetry` skips `MFA_REQUIRED`.
- 2026-10-09 T-28-3 built (backend dd4907e; docs 4fc1bfe decision 0026 proposed; privacy 23 tests incl. 6 new; full suite 1665 pass, 1 fail = RLS coverage on T-28-2's in-progress `password_history`; scratch-DB run: dry run 1, real run 1, rerun 0). Keeps order/item/shipment rows, money, dates, order numbers; item titles and refund notes kept and flagged for counsel (OI-19). Reviewer (fable) and security (opus) started; compliance after.
- 2026-10-09 T-28-2 built (backend 074c922 migration 0042: `sign_in_failures`, `password_history`, `users.mfa_grace_starts_at`; e42b38d; docs d57c482 decision 0025 proposed; 16 new tests; real run 23/23 checks; full suite 1 fail: `rls-coverage.test.ts` needs the two new global tables in `GLOBAL_TABLES`, the security-reviewer's file, to be granted in its co-review). Migration 0042 applied to the dev DB (additive). Reviewer (fable) started.
- 2026-10-09 T-28-3 security r1 changes-required: only decision 0026's text (item_artwork is PII, not "keep"; add a labels row). Found S-56 (Medium, older than this card): `item_artwork.values` keeps buyer personalization text forever; proof `it.fails` in backend ecff989, docs 044edf8. Code fix is its own card: backlog B-293 (due 2026-11-08), recommended first in wave 29; the wave holds 5 cards. T-28-4 (web, sonnet) started on the :3000/:5173 slot.
- 2026-10-09 T-28-3 reviewer r1 approve (probe and mutation checks: fences hold, order/item/shipment counts unchanged). Round 2 (docs 6bc2d27, decision 0026 text only). Security r2 approve (docs 9d3eb19: 0026 security-accepted, DPP 18-month row now Partial). Compliance co-review started.
- 2026-10-09 T-28-3 compliance r1 approve (docs a1a586f: 0026 accepted). **T-28-3 approved.** Compliance: personalization text is buyer PII under the 30-day purge (input for B-293); staff and refund notes are free text to check in B-293; 0026's keep list added to OI-19 for counsel.
- 2026-10-09 T-28-2 security co-review started (grant: add the two global tables to `GLOBAL_TABLES` in `rls-coverage.test.ts` if it agrees they're global). T-28-4 built (web 4559618; 172 tests incl. 14 new; build ok; headless script 34 assertions; PIDs 34279/34309/34281/34296 stopped; gaps: reset-page reuse and vendor case unit-tested only). Reviewer (opus) started; security co-review (sonnet) after.
- 2026-10-09 T-28-4 reviewer r1 approve; security r1 approve (Low notes: `/\host` return path guard; raw `"PASSWORD_REUSED"` literal in two files; banner links to /account not the section). **T-28-4 approved.**
- 2026-10-09 T-28-2 reviewer r1 (fable) approve (probe: identical status sequence for known and unknown emails; no session when locked; vendor never required; no table rewrite). Note: seeded companies are `demo: true`, so seeded logins are never required; the owner sees the feature only on a newly signed-up shop. Security r1 changes-required: S-57 (Medium, the lock is checked before the password but counted after, so a parallel burst tests far more than 10 passwords) and S-58 (Medium, demote and re-promote restarts the grace forever); proofs `it.fails` in backend b2b9565, docs 18773fe; `GLOBAL_TABLES` grant applied by security. Round 2 (backend-foundation, opus) fixes only S-57, S-58 and the 0025 text, with a two-marker grant in `tenancy/security.test.ts`.
- 2026-10-09 T-28-2 round 2 (backend 03998af migration 0043 `users.mfa_required_since`, 95324fe; docs f1e34f8): attempts counted before the password check; grace restarts at most once per user; proofs flipped to `it`; full suite 1670 pass + 1 expected fail (S-56). Migration 0043 applied to the dev DB. Security r2 started. Reviewer r1 notes went to backlog B-294..B-297.
- 2026-10-09 T-28-2 security r2 approve (bursts of 40: at most 10 passwords tested, same for unknown emails, one email; demote/deactivate/re-promote cycles stay blocked; accepted gap: a user already required before 0043 can get one more grace through a new invite, once). Docs 5673f47: S-57, S-58 fixed; 0025 accepted. **T-28-2 approved. Every wave 28 card is approved** (each required reviewer's latest file says approve). The security proof tests (b2b9565, ecff989) were accepted by the feature owners, who flipped or kept their markers as granted. Gate started: `OPENAI_API_KEY= ANTHROPIC_API_KEY= IMAGE_GEN_PROVIDER= caffeinate -i pnpm gate invai-contracts invai-backend invai-web`.

## Retro
- What slipped:
- Lessons added (links to `team/lessons.md`):
