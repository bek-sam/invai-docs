# Review of T-2-4 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: web-engineer on Opus 5.5
- Verdict: approve

Review range: invai-web `23f0552` (T-2-4, on top of `e37e716` T-2-2), invai-backend `e399249` HEAD
(T-2-3's `3c45e05`/`240a19e` plus T-2-5's `e399249`, used only to run the API; T-2-5's changes are
outside this card).

## Setup
Worktree next to the repos: `git -C invai-web worktree add ../invai-web-r24 23f0552`,
`node_modules` symlinked. API on invai-backend HEAD, port 3294, `REDIS_URL=redis://localhost:6379/14`,
against `invai_r24_copy` (`docker exec local-postgres-1 createdb -U invai -T invai invai_r24_copy`,
already seeded via the template). Web on port 5294 (`VITE_API_URL=http://localhost:3294`). Mailpit
on :8025 (pre-existing). All stopped/dropped/flushed at the end (see bottom).

## Evidence I re-ran
| Command | Result |
|---|---|
| `node_modules/.bin/tsc --noEmit` (invai-web-r24) | exit 0 |
| `node_modules/.bin/biome check src scripts` | Checked 107 files, no fixes |
| `node_modules/.bin/vitest run` | 9 files, 47 tests passed |
| `node_modules/.bin/vite build` | built in 1.21s (pre-existing >500 kB `env` chunk warning, unrelated to this diff) |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-web-r24 e37e716` | "Result: no hits" (deletions, skips/only, assertions removed vs added 0/29, snapshots, config, test-only branches: all clean) |
| `git -C invai-web diff --stat e37e716 23f0552` | 24 files, all under owned paths (see Checks) |

Matches the author's report numbers exactly.

## Exercised for real (live, browser automation via Playwright against my own API/web ports)
- **Sign-up → verify:** fresh sign-up, real Mailpit email ("Confirm your email for InvAI"), followed
  the real `/verify-email?token=` link → success page → session refreshed, banner gone.
- **Forgot password enumeration:** submitted an unknown email and a known email
  (`owner@desertbloom.test`) back to back; both returned the identical "If that email has an
  account…" state in ~53–56 ms with no observable timing gap.
- **Reset password:** real Mailpit link → set a new password → "signed out everywhere" page → old
  password rejected, new password accepted (verified via a live sign-in call). Reusing the same
  link afterward correctly falls back to `INVALID_TOKEN` handling once submitted (see security
  co-review for the URL-token note — non-blocking here).
- **TOTP end-to-end:** enabled 2FA (password confirm → QR/setup key → independent RFC 6238 code
  computed from the setup key → accepted), saw the 10 backup codes once, signed out, signed back in:
  wrong code rejected with "That code is wrong", correct code accepted, landed on `/today`.
- **Backup codes:** signed in with a fresh backup code (successful), then replayed the same code →
  "That backup code is wrong or was already used." (rejected, matches AC3).
- **Sessions/revoke:** confirmed at the API primitive the UI calls
  (`authClient.revokeSession({token})` → Better Auth `/api/auth/revoke-session`): signed in as
  `office@desertbloom.test` from two independent cookie jars, `get-session` for jar B returned a
  live session, revoking B's token from jar A's session immediately made jar B's `get-session`
  return `null`. The UI's per-row "Sign out" button in `sessions-section.tsx` calls this exact
  primitive with the row's `token`; I did not independently re-verify which literal button revokes
  which literal row in the browser (the account DB copy already carried a few stale sessions
  unrelated to this diff), but the underlying call and its effect are proven.
- **`EMAIL_NOT_VERIFIED` dialog:** flipped `owner@desertbloom.test.email_verified` to `false` in the
  DB copy, signed in, clicked "Manage billing" (`billing.portal`, a gated procedure) → got both the
  "Confirm your email first" dialog and a separate bottom-right toast ("Verify your email before
  paying…") at the same time — confirms the author's own noted decision (screenshot 39/40 in the
  report). See the product-designer file for the UX call on this.
- **Vendor `/account` access:** signed in as `vendor@suncitydtf.test`, landed on `/vendor` as
  expected, navigated directly to `/account` — it renders (the `_app.tsx` `shared` allowlist change)
  and shows only that user's own profile/password/2FA/sessions, nothing company- or tenant-scoped.
  Confirmed safe: `account.tsx` and its sections only read `useAuthSession()` (Better Auth's own
  session) and `listSessions()` (the caller's own sessions) — no `me`/company queries added.
- Restored `owner@desertbloom.test.email_verified` to `true` before dropping the DB copy.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Forgot link, neutral answer, reset with clear expired/used errors | Yes | Live: enumeration-safe timing above; reset flow works; code review confirms `INVALID_TOKEN`/`TOKEN_EXPIRED` both map to the "This link doesn't work anymore" state (`reset-password.tsx`) |
| 2 Verify page success/failure; translated banner+resend; `EMAIL_NOT_VERIFIED` prompt | Yes | Live signup→verify; live `EMAIL_NOT_VERIFIED` dialog on `billing.portal` |
| 3 MFA sign-in, code or backup code | Yes | Live TOTP and backup-code sign-in, including wrong-code and reused-backup-code rejection |
| 4 Account page: name/language, password, TOTP w/ QR+backup codes once, sessions+revoke | Yes | Live TOTP setup end-to-end; revoke primitive proven live (see above); password-change form reviewed (`password-section.tsx`, sends `revokeOtherSessions: true`, wrong-current-password path present) |
| 5 en/es, 390 px, keyboard | Yes | `i18n/en.ts`/`es.ts` added in lockstep (138/143 new lines — es has a few extra plural/interpolation variants, no missing keys found by inspection); every new interactive element is a native `<input>`/`<button>`/`<label htmlFor>` or a `Link`, and dialogs use the shared `@invai/ui` Dialog (Radix) already used elsewhere in the app |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat e37e716 23f0552`): `routes/{login,signup,forgot-password,reset-password,verify-email}.tsx`, `routes/_app/account.tsx`, `features/account/**`, `lib/auth.ts`, `i18n/{en,es}.ts`, plus the documented extras — `app-frame.tsx` (user-menu block only: diff is the `UserCog` menu item + the locale-save side effect on the existing language radio group, nothing in T-2-2's banner area), `_app.tsx` (2 hunks: mount `VerifyEmailBanner`, add `/account` to the vendor-shared allowlist), `lib/errors.ts`/`errors.test.ts` (7-line `EMAIL_NOT_VERIFIED` mapping, placed after T-2-2's commit as the author states), `routeTree.gen.ts` (generated from the new routes), `scripts/i18n-es.json` (the i18n build artifact for the new es keys). All justified in the report; none is scope creep.
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened — scan script clean, 0 assertions removed vs 29 added, no `.skip`/`.only`, no mocks of the unit under test
- [x] Tenancy n/a (web-only, no DB); idempotency n/a; money n/a; en/es text present for every new string I sampled
- [x] Decisions recorded: the report documents each out-of-owned-path touch and why; no new decision needed from me

## Optional notes (not blocking)
- The reset/verify-email token stays in the address bar (`?token=…`) through success and on a
  second visit to the same link; see the security-reviewer file for the detail and a suggested
  follow-up (Low, not a blocker — tokens are already single-use server-side).
- The double toast + dialog on `EMAIL_NOT_VERIFIED` (Billing, Shipping) is a real UX redundancy the
  author flagged themselves; product-designer's file has the call.
- Seed users all default to `locale: "en"`, so a Spanish-browser seed user still sees English until
  they pick Español once (author-acknowledged, and it's a seed-data property in invai-backend, not
  something this web-only card can fix).
- `pnpm e2e` was correctly not run by the author (qa-engineer owns uncommitted e2e edits in the
  shared tree); I did not run it either, for the same reason. This should happen at the QA/wave
  gate as the report says.

## Processes and data
- Stopped: API :3294 and web :5294 (I found the API process had died silently once mid-session —
  unrelated to the diff, likely an environment hiccup — and restarted it on the same port before
  continuing).
- Dropped `invai_r24_copy`; flushed Redis db 14.
- Removed the worktree `../invai-web-r24` and temp scripts (`/tmp/t24r`, `invai-web/tmp-r24-review`).
- `owner@desertbloom.test.email_verified` restored to `true` before the DB copy was dropped.
