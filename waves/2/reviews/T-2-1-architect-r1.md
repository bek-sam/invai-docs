# Review of T-2-1 (round 1)

- Reviewer: architect on Fable
- Author: backend-engineer (billing) on Opus 5.5
- Verdict: approve

## Evidence I re-ran
Same worktree/setup as the primary reviewer (`5d80c52`, `invai_test_r21`).

| Command | Result |
|---|---|
| `./node_modules/.bin/tsc --noEmit` | exit 0 — the backend typechecks against the contract's
  `billing.checkout`/`.portal`/`COMMON_ERRORS` stubs this card fills in |
| `./node_modules/.bin/vitest run src/modules/billing` | 31/31 passed |
| Read `invai-contracts/src/contract/billing.ts`, `src/schemas/billing.ts`, `src/contract/_base.ts`
  directly (read-only; contracts isn't this card's path, so I'm checking use, not editing) | see below |
| Live exercise: `GET /billing/` on port 3291 against `invai_r21_copy` (dropped after) | response
  shape matched `BillingStatus` field-for-field: `plan`, `usage`, `status`, `trialEndsAt`,
  `currentPeriodEnd`, `cancelAtPeriodEnd`, `paymentsEnabled`, `overLimitBehavior` |

## Contract use
- `billing.checkout` (`POST /billing/checkout`, `billing.manage`, input
  `z.union([{plan}, {pack: z.string()}])`, output `{url: z.url()}`) — implementation matches exactly:
  `checkout()` in `service.ts` validates `plan` against `isSelfServePlan` and `pack` against
  `isPackKey`, both server-side, and returns `{url}` only, never touching plan state. Never calls a
  variant the contract doesn't define.
- `billing.portal` (`POST /billing/portal`, output `{url: z.url()}`) — matches.
- `billing.changePlan`'s live-Stripe behavior (downgrade to free / cancel at period end / else
  `PAYMENT_REQUIRED`) matches the card and the wave's agreed interface note precisely; mock behavior
  is unchanged, so T-2-2's demo path and any existing mock-mode consumer keep working.
- **Error codes**: `PLAN_LIMIT_REACHED`, `PAYMENT_REQUIRED` both used through the typed helpers
  (`planLimit`, `paymentRequired` in `lib/errors.ts`) whose `data` shapes (`{meter,used,limit}`,
  `{checkoutUrl}`) match `COMMON_ERRORS` in `contract/_base.ts` exactly, field for field — confirmed by
  reading both files side by side, not assumed. `EMAIL_NOT_VERIFIED` is T-2-3's to use; this card
  doesn't throw it, which is correct (nothing in the card asks for it).
- **`BillingStatus` additive fields**: `currentPeriodEnd` and `cancelAtPeriodEnd` are both
  `.optional()` in the schema (so existing callers don't break) and the implementation always
  populates them (never omits), which is the stricter, safer direction. `status` includes
  `trial_expired`, spelled and cased identically to the schema and to `SUBSCRIPTION_STATUSES` in
  `db/schema/billing.ts` — no `"canceled"`/`"cancelled"` mismatch (the plan review's caught issue is
  not reintroduced).
- **`billing_webhook_events` vs. reusing `webhook_deliveries`**: implementation follows the plan
  review's fix exactly — a new table, not a `CHANNELS` enum widened to include `stripe`. Grepped
  `invai-contracts/src/states.ts` `CHANNELS` — still `etsy | amazon | shopify | tiktok | walmart |
  ebay | csv`, unchanged by this card. `POST /webhooks/stripe` is registered as its own Hono route,
  ahead of `/:channel`, not a case reachable through the generic dispatcher.
- **Scope discipline**: this card makes no edits inside `invai-contracts/**` (confirmed:
  `git diff --stat` across the three reviewed commits touches only `invai-backend`). It consumes the
  stubs the architect already committed, as the wave plan requires.

## Acceptance criteria (contract-relevant subset)
| # | Met? | Evidence |
|---|---|---|
| 1 checkout | Yes | Input/output match contract exactly; live-exercised |
| 2 webhook | Yes | Own route, dedupe table separate from `webhook_deliveries`/`CHANNELS`, matches plan review |
| 6 limits | Yes | Error `data` shape matches `COMMON_ERRORS.PLAN_LIMIT_REACHED` exactly |
| 8 paymentsEnabled | Yes | `BillingStatus.paymentsEnabled` populated correctly |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed — no `invai-contracts/**` edits in this diff
- [x] Nothing outside scope
- [x] Tests exercise the behavior; no weakening found in this card's files
- [x] Contract stays additive: new optional fields only, no renamed/removed fields, `CHANNELS` untouched
- [x] Decisions recorded where needed (plan review already documents the dedupe-table decision)

## Optional notes (not blocking)
- `billing.checkout`'s `pack` input is still `z.string()`, not a typed enum — the card's own "Added by
  the stub review" AC 10 only requires the *backend* to validate against known keys (it does,
  server-side, via `isPackKey`), which is met. A `PACK_KEYS` contract enum was already flagged by the
  author as a follow-up for the architect in `wave.md`; agreed it's worth doing before T-2-2 hardcodes
  the same two strings on the web side, but it's not a gap in this card's acceptance criteria.
