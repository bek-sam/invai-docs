# Review of T-2-0 wave-2 contract stubs (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: architect on Sonnet 5 (contracts, backend stub); web fix commit also Sonnet 5 (per `Co-Authored-By`)
- Verdict: **approve**

Commits reviewed (all local on `main`, not yet pushed):
- invai-contracts `a3b4067`: billing `checkout`/`portal`, `BillingStatus` changes, `PAYMENT_REQUIRED` and `EMAIL_NOT_VERIFIED`, `PO_STATES.submitting`, `user.invited` payload
- invai-contracts `1a22b29`: optional `idempotencyKey` on `ReceiveInput` (wave 1, T-1-3 stub)
- invai-backend `d97cd3c`: `NOT_IMPLEMENTED` handlers for `billing.checkout` and `billing.portal`
- invai-web `dc9f655`: `PoStatusBadge` `submitting` tone plus en/es `poState.submitting`

There's no task card for this work. I judged it against `wave.md` "Agreed interfaces" and `reviews/plan-architect-r1.md`.

## Evidence I re-ran
| Command | Result |
|---|---|
| `invai-contracts: pnpm typecheck` | exit 0 |
| `invai-contracts: pnpm lint` | `Checked 46 files ... No fixes applied.` |
| `invai-contracts: pnpm test` | 4 files, 31 tests passed |
| `invai-backend: pnpm typecheck` | exit 0 |
| `invai-web: pnpm typecheck` | exit 0 (TS7053 on `po-badge.tsx` from the architect review is fixed by `dc9f655`) |
| `invai-floor: pnpm typecheck` | exit 0 |
| `invai-web: pnpm build` | exit 0, `✓ built in 1.03s` (only the existing chunk-size warning) |
| `invai-backend: pnpm vitest run src/api/authz.test.ts src/modules/billing` | 2 files, 10 tests passed |
| `scan-test-weakening.sh` on contracts (base `11f53f5`), backend (`659f1bc`), web (`d6336e0`) | `Result: no hits` in all three |
| `git diff --stat <base> HEAD` in each repo | contracts: 6 `src/` files, +48/−3; backend: `src/modules/billing/router.ts` +8; web: `po-badge.tsx`, `i18n/en.ts`, `i18n/es.ts` +8/−2 |
| Own API `PORT=3191 pnpm dev:api` (mocks on), signed in as owner@ and office@ | see next rows; stopped afterwards, port 3191 free |
| `POST /api/v1/billing/checkout {"plan":"pro"}` as owner | `501 NOT_IMPLEMENTED "billing.checkout is not implemented yet"` |
| `POST /api/v1/billing/portal {}` as owner | `501 NOT_IMPLEMENTED` |
| same two calls as office@ (no `billing.manage`) | `403 FORBIDDEN {"permission":"billing.manage"}` |
| `POST /api/v1/billing/portal` with no session | `401 UNAUTHORIZED` |
| `POST /api/v1/billing/checkout {}` as owner | `400 BAD_REQUEST`, `invalid_union` (needs `plan` or `pack`) |
| `GET /api/v1/billing/` as owner | `200`, `"status":"active"`; the widened output schema validates today's backend response |
| `grep -rn "user.invited"` in all repos except `node_modules` | 1 hit: the definition in `invai-contracts/src/events.ts:18` |
| `grep PoState\|PO_STATES` in backend, web, floor and ui | web `po-badge.tsx` (now `Record<PoState, …>`, exhaustive), web `purchase-orders.index.tsx:97` (`PO_STATES.map`, not exhaustive); backend only has comments |
| `grep trialing\|past_due\|trial_expired\|SUBSCRIPTION_STATUSES` | backend DB enum `["trialing","active","past_due","cancelled"]`, a subset of the new contract enum; web `billing.tsx:55-63` uses a ternary with a `danger` fallback and a `t()` default (not exhaustive) |

## Acceptance criteria (from wave.md "Agreed interfaces")
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | `billing.checkout({ plan }) -> { url }`, `billing.manage`, `POST /billing/checkout`. It also accepts `{ pack }`, which T-2-1 AC7 and T-2-2 AC4 need. The stub returns 501 and never changes the plan. |
| 2 | Yes | `billing.portal() -> { url }`, `billing.manage`, `POST /billing/portal`. The stub returns 501. |
| 3 | Yes | `BillingStatus.status` adds `trial_expired` and keeps the `"cancelled"` spelling. `trialEndsAt` already existed. `currentPeriodEnd` (nullable, optional) and `cancelAtPeriodEnd` (optional) are new. All output-side and additive. The backend DB enum is a subset, so no runtime output-validation failure (checked live: `GET /billing/` 200). |
| 4 | Yes (doc only) | The `changePlan` doc comment describes the `PAYMENT_REQUIRED` rule. Behavior is T-2-1's job. |
| 5 | Yes | `PAYMENT_REQUIRED` (402, data `{ checkoutUrl: url \| null }`) and `EMAIL_NOT_VERIFIED` (403) are in `COMMON_ERRORS`. `PLAN_LIMIT_REACHED` was already there. Additive. Nothing keys a `Record` on the error codes (grep). |
| 6 | Yes | `PO_STATES` gains `submitting` at the end. Every consumer typechecks. The web badge map is now an exhaustive `Record<PoState, …>` with en "Submitting…" and es "Enviando…". The backend still coerces `submitting` to `draft` (`inventory/service.ts:852`), so the new state can't reach the web yet. |
| 7 | Yes | `user.invited` is now `{ orgId, invitationId }`. It's not additive, but nothing emits or subscribes to it in any repo (grep, 1 hit = the definition), so nothing breaks. |
| 8 | Yes | `ReceiveInput.idempotencyKey`: optional, 8–128 chars, additive. The backend uses it (`inventory/service.ts:1276-1344`, covered by `po-safety.test.ts:343-384`). |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`git diff --stat`): contracts `src/` (architect), backend `modules/billing/router.ts` (stub the architect review announced), web `po-badge.tsx` and i18n (web-engineer's same-day consumer fix)
- [x] Nothing outside scope: everything maps to an agreed-interface line
- [x] Tests: no tests changed, and the scan found no hits in any of the three repos. These are stubs with no behavior to test. I exercised the stubs live instead (501, 403, 401, 400).
- [x] Tenancy: no new tables and no `withSystem`. The stubs don't touch data. Idempotency: n/a (stubs), and `ReceiveInput.idempotencyKey` is covered by the backend. Money: n/a. en/es: `poState.submitting` is in both.
- [x] Decisions recorded where needed: the `user.invited` breaking change is justified in `plan-architect-r1.md` and in a code comment. No ADR is needed while nothing consumes the event.

## Optional notes (not blocking)
1. **Push order:** contracts `a3b4067` must be pushed together with web `dc9f655`. Pushed alone, web CI (which checks out sibling repos) fails typecheck with TS7053.
2. **PO filter (backend owner, later card):** `purchase-orders.index.tsx:97` now lists a "Submitting…" filter option. Choosing it sends `status: ["submitting"]`. The backend returns the in-flight POs but relabels them `draft` (`service.ts:852`), so a "Submitting" filter shows rows badged "Draft". This is rare and harmless. It goes away when the backend drops the coercion at `service.ts:852` and the `draft → +submitting` filter widening at `service.ts:906-908`. The comments at `db/schema/inventory.ts:145` and `service.ts:851` ("until contracts PO_STATES has it") are now stale.
3. **T-2-2:** `billingStatus.trial_expired` has no en/es string yet. The web falls back to the raw "trial expired" in both languages. The backend can't return it until T-2-1 adds it to `SUBSCRIPTION_STATUSES`, so T-2-2 must add both strings.
4. **T-2-1:** `checkout` input `pack: z.string()` has no length limit. Use an enum of pack keys, or at least `.max()`, when the packs are defined.
5. `EMAIL_NOT_VERIFIED` and `FORBIDDEN` both use HTTP 403. The web must branch on `error.code`, not the status (T-2-4).
6. `NOT_IMPLEMENTED` isn't a declared error (`defined:false`, 501). That's fine for a stub. T-2-1 replaces it.
7. The web receive form doesn't send `ReceiveInput.idempotencyKey` yet, so a double-submitted receipt from the UI isn't deduped until a web card sends one.
