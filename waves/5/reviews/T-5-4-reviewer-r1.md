# Review of T-5-4 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: web-engineer + backend-foundation on Opus 5.5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend log --oneline -1` / `diff --stat c56242a~1 c56242a` | `c56242a` on `main`; 9 files: `drizzle/0018_*`, `db/schema/tenancy.ts`, `integrations/vendors/mailer.ts`, `modules/tenancy/{invites,pin-only}.test.ts`, `modules/tenancy/{router,service}.ts` |
| `git -C invai-web log --oneline -1` / `diff --stat 7bf4b3d~1 7bf4b3d` | `7bf4b3d` on `main`; `routes/_app/settings/{team,stations}.tsx`, `i18n/{en,es}.ts`, `scripts/i18n-es.json` |
| `git -C invai-ui log --oneline -1` / `diff --stat eaad60d~1 eaad60d` | `eaad60d` on `main`; `i18n/locales/{en,es}.json` (+`station.receiving`) |
| `git -C invai-floor log --oneline -1` / `diff --stat effa695~1 effa695` | `effa695` on `main`; `app/{actions,store}.ts`, `hooks/{useRealtime,useStationQueue}.ts`, `realtime/sse.ts`, `screens/{LoginScreen,SetupScreen}.tsx`, `i18n/{en,es}.ts`, new `app/stationRemoved.test.ts` |
| Mechanical checks, worktrees `<repo>-t54review` @ each SHA, symlinked `node_modules` (delegated to a fresh general-purpose agent, results spot-checked below) | backend: `tsc` clean, `biome check .` clean (251 files); web: `tsc`/`biome` clean, `vitest run` 13 files/75 passed, `vite build` ok; ui: `tsc`/`biome` clean, `vitest run` 4 files/20 passed; floor: `tsc`/`biome` clean, `vitest run` 8 files/86 passed, `vite build` ok |
| Own re-run, backend main tree, `TEST_DATABASE_URL=…/invai_test_t54_review`, `REDIS_URL=…/13`, `vitest run` | **67 files, 480 tests passed** (matches the report and the delegated worktree run) |
| `.claude/skills/independent-review/scan-test-weakening.sh <repo> <prev-sha>` × 4 | backend: 1 hit (2 removed assertions in `invites.test.ts`) — read below, not weakening; web/ui/floor: no hits |
| Live pass: DB copy `invai_t54_r1_copy` (`createdb -T invai`, `db:migrate` → up to date, `pin_only` column and `invitations_pending_org_email_unique` index present), API `:3194` (`REDIS_URL=…/12`, `DATABASE_URL`→copy, `WEB_ORIGIN=:5194`), Mailpit, seed's `Desert Bloom Tees` set `demo=false` on the copy only (it seeds `demo=true`, which silently skips invite mail — see Optional notes) | see below |

**Live pass, curl-driven (API-level; browser/floor screens verified via the report's screenshots and the floor test suite instead of a fresh Playwright run, for time):**
- Owner signed in. `POST /team/invite {name,role:"packer",pinOnly:true}` → 200, `email` is `pin+<uuid>@floor.invai.internal`, `pinOnly:true`, `status:"active"`. `POST /team/<id>/pin {pin:"5599"}` → `{ok:true}`.
- Issued a token for station "Pack 1". `POST /floor/login` with that token + PIN `5599` → 200 session, `user.role:"packer"`.
- `POST /api/auth/sign-in/email` with that same placeholder address + any password → **401**, no `session_token` cookie set. Matches AC1.
- `POST /team/invite` to a fresh email, twice → second call returns the **same invitation id** (resend, not a duplicate row); `POST /team/<id>/resend` → 200, same id, `status:"invited"`. `POST /team/<id>/revoke` → `{ok:true}`; a second `revoke` on the same id → **409 NOT_INVITED** (idempotent). Matches AC2.
- Sole owner: `POST /team/<ownerId>/role {role:"admin"}` → 400 "You cannot change your own role"; `POST /team/<ownerId>/deactivate` → 400 "You cannot deactivate yourself". Matches AC3's "self" path; the `activeOwnerCount()<=1` CONFLICT branch (a second owner acting on the last remaining owner) is exercised by no test in the whole suite (`grep -rn "at least one owner" **/*.test.ts` → no hits) — pre-existing gap, not introduced here, noted below.
- Station "Pack 1": `floor/staff` with its token → 200 before, **401 "Station token required"** immediately after `DELETE /stations/<id>/token`. Matches the API half of AC4; the floor-side "goes to setup" behavior is covered by `stationRemoved.test.ts` (4 new tests, re-run above) plus the report's screenshots (`7-floor-removed-en.png`, viewed).
- Cleanup: killed my API (port 3194 free), dropped `invai_t54_r1_copy` and `invai_test_t54_review`, flushed Redis dbs 12 and 13, confirmed no `t54`-named worktrees remain.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 PIN-only staff: name+PIN, no email, floor sign-in, no web sign-in, appears in team list | Yes | Live pass above; `pin-only.test.ts` (5 tests); `3-team-en.png`/`4-floor-pin-only-signed-in.png` viewed |
| 2 `team.resend`/`team.revoke` wired; one pending invite per company+email (DB index); "earlier invite pending" UI | Yes | Live pass above; `invitations_pending_org_email_unique` on the copy; `service.ts` catches `23505`→`CONFLICT`; `team.tsx`'s `earlierPending`/`team.earlierPendingHint`; `1-earlier-pending-en.png` viewed |
| 3 Confirmations on role/deactivate/revoke; last owner can't be demoted or deactivated | Partially — see blocking finding 1 (revoke, not confirmations) | `ConfirmDialog` wired for role/deactivate/revoke in `team.tsx`; last-owner self-guard verified live; `changeRole`'s guard pre-dates this card (`service.ts:524`, confirmed via `git show c56242a~1`); `setMemberStatus`'s guard also pre-dates it (`service.ts:571-576`, confirmed) — the card's job was "verify and add if missing," and verification was correctly done, just not exercised end-to-end by a test |
| 4 Stations: edit name/kind, revoke token, last-seen time | Yes | `stations.tsx` `EditStation`/revoke confirm; live pass above; `tablet-after-revoke.png` (not opened, redundant with the API check and `7-floor-removed-en.png`) |
| 5 Quality: en/es, 390px, keyboard accessible | Yes | `en.ts`/`es.ts` key sets match 1:1 (diffed, 39/39) for web; floor's one new key present on both sides; `team.roleFor` aria-label added; `sr-only` PIN-column fix explained and screenshotted at 390px (`5-stations-es-390.png`, `6-add-pin-only-es-390.png`, viewed) |
| 6 `station.receiving` i18n | Yes | `invai-ui` diff, both locales |

## Blocking findings
1. `invai-backend/src/modules/tenancy/service.ts:434-439` (`revokeInvite`) — the final `UPDATE` has no `WHERE status = 'pending'` guard, unlike its sibling `resendInvitation` at `service.ts:369-373`, which does (`.where(and(eq(id,…), eq(status,"pending")))`). `revokeInvite` reads the row through `pendingInvitation` (status-filtered `SELECT`) but then writes unconditionally by id. Failure scenario: an owner clicks **Revoke** on an invited row at the same moment the invitee finishes accepting it (Better Auth's own `acceptInvitation`, which runs outside this transaction and flips `status` to `accepted` plus creates the `members` row). If revoke's `SELECT` reads the row while still `pending` but its `UPDATE` commits after accept's transaction, revoke silently overwrites `status` back to `canceled` on a row that is actually accepted — the person is a fully active member, but the invitation audit trail now falsely shows "revoked," and `team.revoke`'s own audit entry ("Invitation to X revoked") is wrong. This is exactly the "revoke racing accept" case the card's checklist calls out, and there is no test anywhere in `invites.test.ts` (including the new `team.resend sends the invite again; team.revoke cancels it` test) that exercises this race — every revoke test acts on a row that's known to still be pending. Fix: add the same `WHERE status = 'pending'` guard used by resend, and return `notInvited()` when it updates zero rows.

## Checks
- [x] Only owned paths changed (`git diff --stat`) — backend touches `integrations/vendors/mailer.ts`, outside the card's literal "Owned paths" list, but the wave.md contract-stub section 4 explicitly directs this file for T-5-4 ("the mailer … must treat `pinOnly` … as never send here"), so it's directed work, not scope creep.
- [x] Nothing outside scope
- [ ] Tests exercise the behavior, and none were weakened — no weakening found (the 2 removed assertions in `invites.test.ts` are a same-strength replacement for the old cancel-and-recreate behavior, now resend-in-place; see Optional notes), but finding 1 shows a real behavior with **no** test coverage
- [x] Tenancy (`withTenant`, RLS on new tables), idempotency, money in cents, en/es text — `addPinOnlyStaff`/`inviteUser`/`revokeInvite` all run inside `withTenant`; `users`/`invitations`/`members` are Better-Auth-owned tables scoped explicitly by `organizationId`/company id in every query touched (no new tenant table added); invite/resend/revoke are each idempotent against retries except for finding 1's race; no money involved
- [x] Decisions recorded where needed — the `pinOnly` design (synthetic placeholder email, no `signUpEmail`) is fully documented in `wave.md` §4 and the card, matching the code

## Optional notes (not blocking)
- `service.ts` `activeOwnerCount()<=1` guard (both `changeRole` and `setMemberStatus`) is itself a TOCTOU race across two concurrent requests from two different owners (read committed, no row lock) — pre-existing from before this card, and genuinely hard to hit in practice (it requires 2 owners racing to deactivate/demote each other down to zero), but zero test in the suite exercises the "another owner touches the last owner" CONFLICT message at all. Worth a follow-up card, not blocking T-5-4.
- Seed's `Desert Bloom Tees`/`Sun City DTF` are `demo=true`, which makes `sendInviteEmail` a silent no-op — this made the gate's Mailpit check for invites pass vacuously unless someone notices (the report already flags this as a cross-card note for T-5-3/seed). I hit the same thing and had to flip `demo=false` on my copy to see mail land.
- `invites.test.ts`'s "re-inviting resends the one pending invite" test removed two `expect` lines for the old cancel+recreate behavior and replaced them with 5 new assertions for the resend behavior (id stability, mail count, expiry, row count) — a strictly stronger check of the new contract, not a weakening. The scan script's hit here is a false positive worth noting for future reviewers of this card.
