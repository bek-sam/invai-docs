# Review of T-19-4 (round 1)

- Reviewer: reviewer on opus
- Author: backend-foundation on fable
- Verdict: **approve**
- Commits reviewed (invai-backend): `0af819a` (day 1), `776697b` (final). Base for diffs: `0af819a~1` (= `bdab237`).
- Worktree: `/Users/bekbolsun/invai/invai-backend-rev-t19-4` at `776697b`, symlinked `node_modules`, test DB `invai_t19_rev_4`, Redis DB 10, API on :3174 against `invai_t19_rev_4_dev` (a migrated copy of the dev DB).

## Evidence I re-ran
| Command | Result |
|---|---|
| `./node_modules/.bin/tsc --noEmit` | exit 0 |
| `./node_modules/.bin/biome check .` | `Checked 364 files … No fixes applied.` exit 0 |
| `vitest run src/lib src/api src/modules/tenancy src/env.test.ts src/db` | `Test Files 1 failed \| 33 passed (34)`, `Tests 1 failed \| 193 passed (194)`. Only red: `authz.test.ts` "vendor users hold only vendor-portal and own-org permissions" |
| Same authz test on `git archive bdab237` (before this card) | also red: `expected [ Array(7) ] to deeply equal [ Array(6) ]`. The test reads the contract only; `me.notifications.*` (`org.read`, contract 0.7.0, T-19-1) adds `me`. Not caused by T-19-4; security-reviewer owns the fix (report "Blocked by other owners" is right) |
| `vitest run src/modules/digest/digest-consent.acceptance.test.ts` (QA) | `Tests 4 passed (4)`: AC23, AC24, AC25, AC26 green. None of its reds are T-19-4's; the remaining digest acceptance reds belong to T-19-3 |
| Mutation: old `if (path[0] === "ai") return "ai"` in `orpc.ts`, run `src/api/buckets.test.ts` | both B-133 tests fail (`2 failed \| 1 passed`); restored, green. The test is load-bearing |
| `drizzle-kit generate --name revcheck` at `776697b` | `No schema changes, nothing to migrate`: `0028_notifications.sql` + snapshot match the schema (generated, not hand-edited); `776697b` does not touch `drizzle/` |
| `scan-test-weakening.sh <worktree> 0af819a~1` | deleted tests none, skips/mocks none, assertions removed=0 added=153, snapshots none, config none, test-only branches none. Its only hits are two untracked `sec4-*proof.test.ts` files another reviewer placed in my worktree during the review; not part of the card |
| tsx probe of `safeWebPath` | `//evil.com`, `/\evil`, `/\/evil.com`, `javascript:alert(1)`, `/javascript:alert(1)`, `https://evil.com`, `/\tevil`, `" /x"`, `""`, `null`, `/a:b` → `/`; `/digests/2026-W39?x=1#a` kept. Redirect is also prefixed with `WEB_ORIGIN` |
| tsx probe of tokens | payload keys `v,k,c,u,r,exp`; unsubscribe TTL 399 d, click 29 d (day-rounded); signing key ≠ `BETTER_AUTH_SECRET`; payload with `u` edited and original signature → `null`; past `exp` → `null` |
| Live: `me.notifications.get/set` as owner on :3174 | get → `{items:[{kind:"digest",on:…,source:"settings"}]}`; set off → on toggles with new `updatedAt`; anonymous → 401 UNAUTHORIZED |
| Live: `sendUserEmail` script, same input twice concurrently + once more | owner: `duplicate` / `sent` / `duplicate`; `email_sends` row `sent`, `sentAt` set. Office (not opted in): `duplicate` / `opted_out` / `duplicate`; row `skipped opted_out` |
| Mailpit `/api/v1/message/:id/headers` | `Message-Id: <digest.rev4….<userId>@invai.local>` (= caller's), `List-Unsubscribe: <http://localhost:3174/l/eyJ…>, <mailto:sheets@invai.local?subject=unsubscribe%20digest>`, `List-Unsubscribe-Post: List-Unsubscribe=One-Click`; footer text ends with the unsubscribe link, Settings link and `InvAI, postal address pending (OI-12), USA` |
| Live `/l/:token` | GET → 302 `http://localhost:5173/unsubscribe?token=…`, pref unchanged; POST (form `List-Unsubscribe=One-Click`) → 200 `{"ok":true}`, pref `f\|unsubscribe_link\|03:06:40.354`; 2nd POST → 200, `updated_at` unchanged; GET again → 302, unchanged; payload `u` edited to another member → POST 400 / GET 302 `?error=invalid`; flipped signature → 400; `abc` → 400; real-key token for a vendor user not in the company → 400; `r:"newsletter"` → 400; click GET (no handler registered yet) → 302 `/`; click POST → 405; preference row count and max `updated_at` unchanged after all bad tokens; Undo JSON → 200 `{"ok":true,"undone":true}`, pref `t\|settings`; 2nd Undo → 409 `not_unsubscribed` |
| Live per-IP bucket | 62 GETs with one `x-forwarded-for` → `60 × 302, 2 × 429`; another XFF → 302 |
| Live B-133 as owner | 25 `ai.credits.balance` → 25 × 200; then `ai.assistant.ask` streams (`start`, `tool_call` …); then 21 more asks → exactly 2 of 22 asks `RATE_LIMITED` (20/min `ai` bucket intact) |
| Log scan | API log and send-script log: 0 occurrences of `eyJ` (no token); `notify`/`links` lines carry ids only. See note 2 for the mailer's pre-existing `to` field |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Preferences per (company, user, kind), default off, admin only off, RLS + isolation | yes | `notify.ts:170-199` (on requires `source: settings`, else `forbidden`); `notify.test.ts` "defaults to off…", "is isolated per company (RLS)"; migration has `ENABLE ROW LEVEL SECURITY` + `*_tenant` policies + `company_id`-leading indexes; `rls-coverage` green; live REST toggle |
| 2 sendUserEmail gates, skip reasons, idempotent, deterministic Message-ID | yes | gates `notify.ts:350-419` (member, placeholder/PIN, verified, suppressed, opt-in; sample workspace via mailer `MAIL_SKIPPED`); kill switch writes no row; claim tx commits before the transport (`notify.ts:451-487`, `sendMail` outside any `withTenant`); `notify.test.ts` skip-reasons/takeover tests; QA AC23/AC26 green; live concurrent double → one `sent` + `duplicate` |
| 3 RFC 8058 headers + footer postal address | yes | Mailpit headers and footer above; `notify.test.ts` header and en/es footer tests |
| 4 Signed links bound to company+user+kind+ref, expiry, tamper rejected, nothing changes | yes | `links.ts` purpose-bound key `hmacHex(BETTER_AUTH_SECRET,"links:v1")`, UUID/ref/exp checks; route binds `c`+`u` to an active membership (`api/links.ts:46-55`); `links.test.ts` both-direction cross-shop test; QA AC25 green; live tamper/real-key-other-user → 400, no row change |
| 5 Public routes: POST idempotent, GET redirect only, click same-origin, per-IP limit, no PII in logs | yes | live results above; `links.test.ts`; `links` bucket 60/min in `ratelimit.ts` (granted); `Cache-Control: no-store` |
| 6 Env switches, safe defaults, none in PRODUCTION_KEYS | yes (see note 4) | `env.ts` diff; `env.test.ts` green; `DIGEST_SUMMARY_MODE` default `shadow` |
| 7 B-133 cheap `ai.*` reads → `reads`; ask stays `ai` | yes | `orpc.ts` `AI_CHEAP_READS`; `buckets.test.ts` (fails on old code, mutation above); live 25 reads + 22 asks |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`git diff --stat`): all under the card's list or grants (`mailer.ts` hunk only adds `messageId?`, `headers?`, `MAIL_SKIPPED` + `mailSkipReason()`, placeholder/PIN skip kept; `ratelimit.ts` per wave.md grant; `db/schema/index.ts` one line). Two doc-sync files outside the card list but inside backend-foundation's role paths: `.env.example` (env comments) and `src/modules/README.md` (two helper rows). Not blocking.
- [x] Nothing outside scope (no digest content, scheduling, deliveries, web, provider or DNS)
- [x] Tests exercise the behavior, and none were weakened (scan clean; B-133 test fails on old code; new modules' tests can't pass without them)
- [x] Tenancy (`withTenant` everywhere, no `withSystem`; RLS + company-leading indexes on the 3 new tables), idempotency (`email_sends` unique `(company_id, dedupe_key)`, pending → sent/skipped/failed, send outside a transaction, concurrent double proven live), money n/a, en/es footer text
- [x] Decisions recorded where needed (ADR 0016 followed; in-card choices listed in the report)

## Optional notes (not blocking)
1. `src/api/app.ts:185` (existing `onError`) logs `path: c.req.path`. For `/l/:token` the path *is* the token, so any unhandled error inside `api/links.ts` (e.g. a Postgres blip in `boundToMembership` or `setEmailPreference`) writes a 400-day link token to the log, against ADR 0016 §2 "Tokens never appear in logs". Impact is small (the token only unsubscribes or undoes one person's digest email) and needs a 500 to trigger, so I leave severity to the security-reviewer. Cheap fix: a try/catch in `links.ts` that logs ids only and answers 500/redirect, or redact `/l/*` in `onError`.
2. `src/integrations/vendors/mailer.ts:78` (pre-existing, outside the grant): `log.info("mail sent", { to: mail.to, … })`. Every person-facing email now logs the member's address (seen live: `[mailer] mail sent {"to":"owner@desertbloom.test",…}`). `notify.ts` itself logs ids only. For integrations-engineer / security-reviewer.
3. `clientIp` (`src/api/context.ts:89`, pre-existing) trusts the first `x-forwarded-for` value, so the per-IP `links` bucket is bypassable by rotating that header (live: a new XFF got 302 after the old one hit 429). Same as every other per-IP limit today; worth a backlog row for proxy-aware IP extraction.
4. `DIGEST_EMAIL_ENABLED` defaults to `true` (report "Decisions" flags it). The wave fence holds today (local Mailpit only, deploys owner-gated, OI-12/13/14 open), but a `false` default would make "no send before OI-12/13/14" hold by config too. Tech lead's call.
5. A `pending` row older than 10 min is taken over; if the process died after the SMTP accepted but before `settle`, the retry sends a second copy (at-least-once). Acceptable and documented; mention it in the digest runbook.
6. Housekeeping: another reviewer placed `src/lib/sec4-proof.test.ts` and `src/api/sec4-iprate-proof.test.ts` (untracked) in my worktree during this review. I left them in place and did not remove the worktree while they exist (see cleanup in my reply).
