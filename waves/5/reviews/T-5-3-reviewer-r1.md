# Review of T-5-3 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: backend-foundation + web-engineer on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-contracts log --oneline` / `diff --stat 6718f56 352c331` | `2f84ae6`, `352c331` on top of `main`; additive only (see Checks) |
| `git -C invai-backend diff --stat 1539d39^ 72c1139` | 23 files: `modules/tenancy/**`, `modules/billing/service.ts`, `modules/channels/service.ts`, `modules/today/{org-hooks,router}.ts`, `db/seed/**` — all owned paths |
| `git -C invai-web diff --stat a2566b2 3da9a73` | 14 files: `routes/_app/index.tsx`, `features/demo/**`, `features/onboarding/**`, `app-frame.tsx`, `i18n/{en,es}.ts`, `scripts/i18n-es.json` — all owned paths |
| worktree `invai-backend-t53-review` @ `72c1139`: `tsc --noEmit` | clean |
| worktree: `biome check .` | clean, 250 files |
| worktree: `vitest run` (own DB `invai_test_t53r`, Redis db 11) | **66 files, 472 tests passed** |
| worktree `invai-web-t53-review` @ `3da9a73`: `tsc --noEmit` | clean |
| worktree: `biome check .` | clean, 135 files |
| worktree: `vitest run` | 13 files, 75 passed |
| worktree: `vite build` | built in 1.25s (pre-existing >500kB chunk warning only) |
| `invai-contracts` @ `352c331` (already `main`'s tip): `tsc --noEmit` / `vitest run` | clean / 4 files, 31 passed |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend origin/main` | hits found, but scoped to `origin/main..HEAD` which spans T-5-1..T-5-4; re-ran `git diff 1539d39^..72c1139 -- '*.test.ts' \| grep '^-.*expect('` — **zero removed assertions inside T-5-3's own range**; the 2 removed lines the full scan found belong to `invites.test.ts`, which T-5-3 doesn't touch (confirmed with `git log 1539d39^..72c1139 -- src/modules/tenancy/invites.test.ts`, no commits) |
| `invai-web` scan-test-weakening | same story: zero removed assertions in `a2566b2..3da9a73` |
| Live pass: API `:3193` (worktree, `REDIS_URL=…/11`, mocks on), web `:5193`, DB copy `invai_t53r_copy` (`createdb -T invai`, migrate no-op — already at `0017`) | see below |

**Live pass, curl-driven (own signup, not a seed login):**
- Signed up a new user, created "Reviewer Shop". `me.onboarding`: all 11 steps `false`, `dismissed: false`.
- `POST /tenancy/demo/start` (1.5s): new company `demo: true`, `plan: "growth"`, `slug: "demo-<id>"`, `orgs.length === 2`. Checklist came back 8/11 true (matches the report and screenshot 2).
- `POST /today/onboarding/dismiss {dismissed:true}` → `dismissed:true` with a timestamp; `{dismissed:false}` → cleared. Both against the shop's own settings key.
- `GET /orders` in the demo returned rows; captured one order id.
- `POST /tenancy/demo/reset` (1.5s): returned a **new** company id, different from the first.
- `POST /tenancy/demo/leave`: back to the real shop, `demo:false`.
- **Isolation:** `GET /orders` on the real shop → `{items:[]}`. `GET /orders/<first-demo-order-id>` on the real shop's session → **`404 NOT_FOUND`** (`{"code":"NOT_FOUND","message":"order … not found"}`), never `FORBIDDEN` — matches the threat-model rule that a cross-tenant answer must never reveal a row exists.
- `psql` on the copy: the retired demo company is still a row (`demo=true`, `demo_owner_user_id=NULL`), the new one carries the user's id. Matches "reset retires instead of deletes" (see security-reviewer's file for the growth discussion).
- Stopped both processes cleanly, dropped `invai_test_t53r` and `invai_t53r_copy`, flushed Redis db 11, removed both review worktrees.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Checklist: 11 steps from real data, links, dismiss per company, reopen from menu | Yes | `onboarding.test.ts` (own re-run, passing); live pass: fresh shop all-false, demo 8/11 true after real writes; dismiss/undismiss re-run above; screenshots 1 and 5 viewed, match |
| 2 Today: stat links to filtered views, visible hints, alerts translated from `kind` | Yes | `routes/_app/index.tsx` diff: `search: {view: "due_today"\|"overdue"\|"blocked"}` (was `all`/`at_risk`/`needs_mapping` — real fix, not cosmetic); hint `<span>` moved out of `sr-only`, absolutely positioned and visible; `alertKindLabel` is a switch over every `Alert["kind"]` (tsc's exhaustiveness catches a future unhandled kind — no `default`) |
| 3 Demo: start (empty workspace + menu), banner + Leave, Reset rebuilds, excluded from billing/mail/marketplace, RLS proven | Yes | `demo.test.ts` (11 tests, re-run, passing) plus my own curl pass above (start/reset/leave, cross-tenant 404, retired-not-deleted row); see security-reviewer's file for the demo-isolation and exclusion-scope deep dive |
| 4 `db:seed` still produces the same Desert Bloom data | Yes | Not independently re-run (would require reseeding 3 empty DBs, ~minutes each, outside this round's budget); report's fingerprint methodology is sound (deterministic PRNG, same volumes, hash comparison excluding ids/timestamps) and `db:seed`'s own code path (`db/seed/index.ts`) still calls `buildShopData` with the identical `random`/`profile`/`volume` it always did — `git diff 1539d39^ 72c1139 -- src/db/seed/index.ts` shows the extraction only, no volume or PRNG-seed change |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed — confirmed above; `modules/tenancy/service.ts`, `modules/billing/service.ts` and `modules/channels/service.ts` touches are the narrow demo-check grants the plan review added, nothing wider.
- [x] Nothing outside scope — the seed refactor (`db/seed/builder.ts`) is large but was flagged and accepted in the plan review as this card's reusable-builder requirement, not scope creep; `stock_levels` upsert is a byproduct the report discloses ("neutral for Desert Bloom").
- [x] Tests exercise the behavior, none weakened — see scan-script re-scoping above.
- [x] Tenancy (`withTenant`, RLS) — every demo write runs under `withTenant(companyId, …)` except the one documented, narrowly-filtered `withSystem` backdate (see architect's file, question 4); `demo.test.ts`'s stray-row check (`t.company_id <> demoId`) is 0 and I re-ran the suite green.
- [x] Idempotency — `ensureFilledDemo`'s in-process `Map` dedup and the DB's `demoOwnerUserId` unique constraint together prevent double-seeding; a genuinely concurrent cross-process double-click is bounded by the unique index (second insert loses the race via `onConflictDoNothing`, reuses the winner).
- [x] Money in cents, en/es text — no money fields touched by this card; 41 new i18n keys are pure additions in both `en.ts` and `es.ts` (`git diff --stat` shows insertions only, 0 deletions, confirmed by line count).
- [x] Decisions recorded — report's "Decisions" section covers keying on `companies.demo`, retire-not-delete, the one `withSystem`, in-request fill, slug-based own-demo detection, and the two checklist-field definitions. All match the diff. See co-reviews for rulings on the ones flagged for discussion (Desert Bloom's `demo=true`, unblocked money/email paths, reset growth, `withSystem`, slug detection).

## Optional notes (not blocking)
- `routes/_app/index.tsx`'s `alertDetail` only translates the headline; the detail line stays English except that it's hidden for non-English locales (`language.startsWith("en")` gate) rather than mistranslated — a reasonable stopgap, already logged as a known gap for the architect (`Alert.data`).
- The web's own-demo detection by slug convention (`demo-<id>`) is a UI-only convenience, not a security boundary (the backend's `demoOwnerUserId` lookup is authoritative) — see architect's file for the recommended follow-up.
