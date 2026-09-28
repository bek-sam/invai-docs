# Review of T-19-4 (round 1)

- Reviewer: security-reviewer on sonnet-5
- Author: backend-foundation on fable
- Verdict: **changes-required**
- Commits reviewed (invai-backend): `0af819a` (day 1), `776697b` (final). ADR: `invai-docs/decisions/0016-signed-link-routes-and-notification-preferences.md`. Report: `invai-docs/waves/19/reports/T-19-4.md`.
- Worktree: `/Users/bekbolsun/invai/invai-backend-rev-t19-4` at `776697b` (shared with the primary reviewer's r1 pass; symlinked `node_modules`), own test DB `invai_t19_sec4`, own Redis DB 9, both dropped/flushed at the end. No API process started (Hono app exercised in-process via `app.request`, no port needed).
- I formed my own threat model before reading `reviews/T-19-4-reviewer-r1.md`; three of my four findings below turned out to match that review's "optional notes" 1–3, which explicitly deferred severity to security-reviewer. This file gives that verdict.

## Evidence I re-ran
| Command | Result |
|---|---|
| `vitest run src/api/links.test.ts src/lib/links.test.ts src/lib/notify.test.ts src/modules/tenancy/notifications.test.ts src/api/buckets.test.ts` | `Test Files 5 passed (5)`, `Tests 27 passed (27)` |
| `vitest run src/api/authz.test.ts src/db/rls-coverage.test.ts src/db/rls.test.ts` | `Test Files 1 failed \| 2 passed (3)`, `Tests 1 failed \| 19 passed (20)`. Only red: "vendor users hold only vendor-portal and own-org permissions" (`authz.test.ts:129`) — caused by `me.notifications.*` (`org.read`, contract 0.7.0, T-19-1) adding `me` to the vendor-reachable namespace set. Read the contract only; not caused by T-19-4. `authz.test.ts` is my owned file; see "Non-blocking, mine to fix" below. `rls-coverage.test.ts` and `rls.test.ts` both green: the three new tables (`notification_preferences`, `email_suppressions`, `email_sends`) have RLS and company-leading indexes |
| Manual read of `notifications.ts`, `router.ts` (`ai` module), confirming `AI_CHEAP_READS`' four procedures (`ai.credits.balance`, `ai.credits.ledger`, `ai.assistant.conversations`, `ai.assistant.conversation`) are plain `withTenant` DB reads with no call into `../../ai/gateway` | Confirmed: B-133 does not let any model-calling procedure escape the `ai` bucket |
| **New test** (own worktree, deleted after): `sendUserEmail` with a spy on `console.log`/`console.error`, assert the recipient's address never appears | **Failed as written** — `[mailer] mail sent {"to":"office-<id>@test.local",...}` is logged. Proves S-36 |
| **New test** (own worktree, deleted after): `POST /l/:token` with `notify.setEmailPreference` mocked to reject, assert the token never appears in logged output | **Passed** — i.e. the leak reproduces: `app.onError`'s "request failed" line contains the raw token, because `c.req.path` for `/l/:token` *is* the token. Proves S-35 |
| **New test** (own worktree, deleted after): 120 requests to `/l/whatever`, each with a distinct spoofed `X-Forwarded-For`, assert none hit 429 | Passed (i.e. the bypass reproduces) — the per-IP `links` bucket never engaged. Proves S-37 (extends existing S-30) |
| **New test** (own worktree, deleted after): `safeWebPath` against `//evil.com`, `///evil.com`, `/\evil.com`, `\\evil.com`, `javascript:alert(1)`, `/javascript:alert(1)`, `http(s)://evil.com`, tab/newline/space-prefixed paths, and a literal `%0d%0a` CRLF-injection string | All correctly reduced to `/`. One case I tried, a literal `/%2F%2Fevil.com` (percent-encoded, not decoded), was *not* rejected — but this is not exploitable: the call site is always `${env.WEB_ORIGIN}${safeWebPath(...)}`, so the scheme+host is fixed text before the path even starts; a browser resolves the result as a path on `WEB_ORIGIN`, never a new origin. No finding |

## Acceptance criteria (my scope: auth, PII, unauthenticated routes, signed tokens)
| # | Met? | Evidence |
|---|---|---|
| 4 Signed links bound to company+user+kind+ref; tamper/cross-shop rejected, nothing changes | yes | `links.ts` payload `{v,k,c,u,r,exp}`; `linkSigningKey()` = `hmacHex(BETTER_AUTH_SECRET, "links:v1")` — a purpose-bound derived key, never the raw secret (grep confirms no other `signPayload`/`verifyPayload` caller in the backend, so no cross-purpose key reuse); `verifyPayload` → `safeEqual` → `timingSafeEqual` (constant-time); `links.test.ts` covers edited payload, wrong key, expiry, v2, bad ids, long ref; `api/links.test.ts` "a token for shop A edited to a person in shop B is rejected and changes nothing" both directions; deactivated-member token also rejected (`resolve()` binds to an *active* membership via `withTenant`) |
| 5 Public routes: POST idempotent, GET never mutates, click same-origin only, per-IP limit, no PII in logs | **partially** | POST/GET behavior, idempotency and same-origin redirect all correct and tested (`links.test.ts`). **No PII/token in logs is not held on the error path** (S-35). **Per-IP limit is trivially bypassed** by spoofing `X-Forwarded-For` (S-37/S-30) — accepted pre-existing gap, but now the *only* control on this route |
| CSRF-ish abuse of the one-click POST | met | POST only ever sets `on:false, source:"unsubscribe_link"` (`setEmailPreferenceTx` refuses `on:true` unless `source:"settings"`); Undo sets `on:true, source:"settings"` only when the current row is `off`/`unsubscribe_link`/within 24 h (`undoUnsubscribe`), else 409/`not_unsubscribed`. No path lets a bare POST turn email on. This is the intended bearer-token-is-the-credential model (RFC 8058); a leaked link letting its holder toggle that one preference is accepted, not a new risk |
| Suppression list / PIN-only placeholders never mailed | met | `claimAndCheck` order: `not_member` → `placeholder` (PIN-only or `isPlaceholderEmail`) → `unverified` → `suppressed` → `opted_out`; `notify.test.ts` exercises every skip reason; no email address is ever stored in `notification_preferences`/`email_suppressions`/`email_sends` (userId only) |
| B-133 doesn't let model-calling procedures escape `ai` | met | see Evidence table |

## Blocking findings
1. **`invai-backend/src/api/links.ts` GET/POST handlers, no try/catch around DB calls** — an unhandled exception (a transient DB error is enough; not hypothetical) propagates to `src/api/app.ts:184-187`'s global `app.onError`, which logs `{ path: c.req.path }`. For `/l/:token`, the token is a path segment, so the bearer credential is written to the log verbatim — the exact thing ADR 0016 §2 says must never happen. Proved with a passing test (mock `setEmailPreference` to reject → the resulting 500's log line contains the raw token). Filed as **S-35** in `security/v1-review.md`. Fix is entirely inside this card's own file: wrap both handler bodies in try/catch, log `{companyId, userId, kind}` only (as the `click` branch already does for its handler call), never `path`. This is cheap and should land before push.

## Checks
- [x] Only owned paths changed (`git diff --stat`) — confirmed by the primary reviewer's r1; I did not re-diff every path, focusing on the security-relevant files (`api/links.ts`, `lib/links.ts`, `lib/notify.ts`, `db/schema/notifications.ts`, `orpc.ts`, `ratelimit.ts`).
- [x] Nothing outside scope for the security surface (no digest content/web changes touched).
- [x] Tests exercise the behavior; scan for weakening not repeated (primary reviewer's `scan-test-weakening.sh` run stands; my own three new tests were additive proofs, deleted after use, never committed).
- [x] Tenancy: RLS + company-leading indexes confirmed on all three new tables (`rls-coverage.test.ts`, `rls.test.ts` green); no `withSystem` in this diff; token binding always goes through `withTenant(p.c, ...)`.
- [x] No token/email/name in Redis keys: `rateLimitKey("links", ip)` → `tb:links:<ip>` — IP only, no PII field.
- [ ] No token/email/name in logs or errors — **not held** (S-35 token-in-error-log; S-36 mailer email-in-log). See findings.
- [x] Decisions: ADR 0016 followed; no new ADR needed.

## Non-blocking, mine to fix (not part of this verdict)
- `src/api/authz.test.ts:129` is red because `me.notifications.*` (`org.read`) is now reachable by the vendor role — intended (a vendor manages its own org's notification preferences), not a bug. This is my owned test file; I will update the expected namespace list (add `"me"` with a comment naming `me.notifications`, contract 0.7.0) directly, outside this review round, since I'm read-only on code for this task. Flagged so the tech lead doesn't wait on it as part of T-19-4's own gate.

## Findings recorded (`invai-docs/security/v1-review.md`)
- **S-35** (High, blocking T-19-4's push) — token leaked into logs via `app.onError` on an unhandled exception in `links.ts`. Owner: backend-foundation. Due: before push.
- **S-36** (High, not blocking T-19-4 — outside its owned/grant paths) — `mailer.ts` logs the recipient's real email address on every send; now exercised weekly, per tenant, by this card's `sendUserEmail`. Owner: integrations-engineer. Due: 2026-10-27 (30-day High clock from today).
- **S-37** (Low, extends the already-Open S-30, not blocking) — the new `links` per-IP bucket is bypassable by spoofing `X-Forwarded-For`, the same root cause S-30 already tracks; new consumer raises its priority. Owner: backend-foundation / platform-sre (see S-30).

## Optional notes (not blocking)
- The `/unsubscribe?token=...` confirm page (T-19-5, out of scope here) puts the bearer token in a URL that a browser will send as `Referer` to any third-party resource that page loads. Recommend T-19-5 set `Referrer-Policy: no-referrer` (or `same-origin`) on that page and avoid third-party trackers/images on it. Not a T-19-4 finding; flagging for the T-19-5 co-reviewers.
- `email_sends`/`notification_preferences`/`email_suppressions` correctly store only `userId`, never an email address — good defense in depth independent of the mailer log issue.
