# Review of T-5-3 (round 1) — security co-review

- Reviewer: security-reviewer on Sonnet 5
- Author: backend-foundation + web-engineer on Opus 5.5
- Verdict: approve

Scope: demo isolation and the exclusion controls (billing, mail, marketplace), plus the contract
stub permission fix (`2f84ae6` → `352c331`). Ownership/style/UI are the primary reviewer's and
product-designer's files.

## Evidence I re-ran
| Command | Result |
|---|---|
| `invai-backend` worktree @ `72c1139`: `vitest run src/modules/tenancy/demo.test.ts src/modules/tenancy/onboarding.test.ts src/api/authz.test.ts src/db/rls-coverage.test.ts` | all passing |
| `grep -n "withSystem(" invai-backend/src/modules/tenancy/demo.ts` (diff files only) | one hit, `fillDemoCompany`'s `runHistory`, with a written reason comment |
| `grep -rn "env.mocks\." invai-backend/src/integrations/{carriers,billing}/index.ts invai-backend/src/modules/channels/service.ts` | see finding 2 below |
| Live pass (same DB copy/ports as the primary reviewer's): started demo, captured its order id, reset, leave, then `GET /orders/<old-demo-order-id>` from the real shop's session → `404 NOT_FOUND` | confirms cross-tenant answers stay `NOT_FOUND`, per `threat-model-change`'s rule |
| `docker exec … psql … -c "select id, demo, demo_owner_user_id from companies where slug like 'demo-%'"` | retired demo row: `demo=true`, `demo_owner_user_id=NULL`; new demo row: `demo_owner_user_id=<user>` — matches "unlink, don't delete" |
| `git -C invai-contracts diff 6718f56 352c331 -- src/contract/tenancy.ts` | permission moved `org.read` → `today.read` between the two stub commits, with the reason in a code comment (vendor orgs hold `org.read`, not `today.read`) |

## Rulings on the two flagged questions

### 1. Desert Bloom gets demo treatment
`isDemoCompany()` (`invai-backend/src/modules/tenancy/demo-flag.ts`) reads `companies.demo` with no
other qualifier, and the seeded Desert Bloom has carried `demo: true` since v1's original seed
(`git log -p -- src/db/seed/index.ts`, present at the file's creation, unrelated to this card).
T-5-3 is the first card to give that flag real behavior: Desert Bloom now silently (a) never
expires its trial (moot — its seeded subscription is `status: "active"`, not `trialing`), (b)
**bypasses `assertWithinPlan`'s limit check entirely, unconditionally**, not only when it would
otherwise pass — `hasPlan()` short-circuits to `{used:0, limit:null, overLimit:false}` regardless
of actual usage, and (c) forces mock Shopify and no-ops invite email, both already moot locally
(no real keys, and `env.mocks.shopify` is already true in dev).

I confirmed with a fork search of both backends' test suites and `invai-web/e2e/`: **nothing today
exercises `PLAN_LIMIT_REACHED` or checks a Mailpit-delivered invite email against the seeded
Desert Bloom company** — both existing test areas build their own fixture companies via
`createCompany()`, and no e2e spec references Mailpit or a plan-limit error at all. So this does
not break any golden-path or smoke check today.

**Ruling: not blocking, but a real design smell that should be fixed, not just noted.** The
report's own decision log discloses this transparently and correctly reasons that the immediate
blast radius is zero. But conflating "this is a per-user sample workspace" with "this company is
flagged `demo` for any reason" is exactly the kind of implicit coupling that breaks quietly later:
the day someone writes the first plan-limit or invite-email smoke test against
`owner@desertbloom.test` (the account every runbook and lesson reaches for), it will silently
no-op instead of failing loudly, and nobody will notice until a real customer's limit doesn't
fire either. **Recommendation for the tech lead: open a follow-up card (architect + QA) to key
the exclusions on `demoOwnerUserId IS NOT NULL`** (the per-user sample workspace, which is what
the card and wave.md's contract text actually mean by "demo company") rather than the bare
`companies.demo` flag, and add one regression test that pins Desert Bloom's real plan-limit and
invite-email behavior so a future refactor can't silently widen the exemption again. This is a
recorded-decision-worthy gap, not a blocker for this round: the acceptance criteria as literally
written ("excluded from billing… emails… marketplace calls") are met by the code, and the
seeded-company overlap is pre-existing, not introduced here.

### 2. Money and email not blocked for demo shops
Confirmed: `invai-backend/src/integrations/carriers/index.ts:12` and
`invai-backend/src/integrations/billing/index.ts:13` pick mock vs. live purely off
`env.mocks.carrier` / `env.mocks.billing` (an environment-wide switch), with **no per-company
demo check** — label buys and Stripe checkout are untouched by this card. `vendors/service.ts:232`
(`deliverInviteMail` without `senders`) is a second, separate vendor-invite email path that
doesn't carry the `demo` flag the way `tenancy/invites.ts`'s `sendInviteEmail` now does.

This is a genuine payments/financial-risk gap, and in a deployment with real Stripe and EasyPost
keys, a demo (sample-data) workspace could buy a real shipping label or start a real Stripe
checkout. **It is currently unexploitable**: this environment has no real keys
(`CLAUDE.md`: "No real API keys exist… chosen automatically when its key is missing"), so
`env.mocks.carrier`/`env.mocks.billing` are true everywhere today regardless of company.

**Ruling: not blocking for this round, but not something to file away either.** The card's owned
paths explicitly narrowed the `billing/service.ts` grant to "only `expireTrials`/
`assertWithinPlan`'s demo check" — the implementer had no grant to touch
`integrations/billing/index.ts`, `integrations/carriers/index.ts`, or `vendors/service.ts`, none of
which are in this card's owned-paths list. Blocking this card for a gap it wasn't scoped to close
would be the wrong lever. Instead: **this must become an owner-inbox entry before any deployment
is ever configured with real Stripe or EasyPost keys** — a demo company spending real money is a
"costly" class of risk per `CLAUDE.md`'s own escalation rule. I'm flagging it here rather than
writing it myself (out of this review's edit scope); the tech lead should file it, tagged for the
billing owner and integrations-engineer, as the report's own "Known gaps" section already
recommends (`isDemoCompany()` check at each of those three call sites). Until that lands, this
platform must not be deployed with real payment/carrier keys while `tenancy.demo` exists.

## Other rulings (checklist items 3, 4, 6)

### 3. Reset (data growth / orphan cleanup)
`retireDemoCompany` unlinks (`demoOwnerUserId = NULL`, deletes `members`) instead of deleting,
because `inventory_movements_append_only` (migration 0001) blocks every `DELETE`, including the
cascade from `companies`, for the `invai_app` role. I verified in the DB copy: the retired row
stays, still `demo=true`, ~50 orders and their items/transitions/timeline entries never removed.
Growth is bounded per reset (~50 orders) and the rows are **not reachable by anyone** once
unlinked — no membership exists, and RLS-gated access requires an active session scoped to that
`company_id`, which requires a membership row. So this is a storage-hygiene issue, not a data
exposure one. Correct call to not weaken the append-only control for sample-data convenience.
Non-blocking; the report's own suggested fix (a sanctioned purge path, security-reviewer decision)
is the right shape for a follow-up — I'd want to review any change to the append-only trigger
itself given what it protects (inventory audit trail integrity), so route that follow-up through
me specifically rather than a generic backlog item.

### 4. `withSystem` for backdating
Justified. The one new `withSystem` call (`demo.ts`'s `runHistory`) exists because
`order_item_transitions` is append-only for the app role — the same constraint applies to the full
seed's backdating, which has always used `withSystem`. It's narrowly scoped: every statement
inside `backdateTimelines` (`db/seed/builder.ts`) filters explicitly on both
`order_id = ${orderId}` and `company_id = ${companyId}`, pinned to rows just built for this one
company in this one call — not a general-purpose escape hatch. `demo.test.ts`'s stray-row check
(`order_item_transitions t … where i.company_id = demoId and t.company_id <> demoId`, expects 0)
is the right test for exactly this risk, and I re-ran it green. Matches
`threat-model-change`'s bar for a justified `withSystem`: pinned scope, written reason, and a test
that would catch a widening.

### 6. RLS isolation proof
Proven, both by the existing test and independently by my own live pass. `demo.test.ts` covers:
no leaked orders either direction between real and demo company (query-level), zero stray
`order_item_transitions` rows outside the demo's `company_id`, and a same-process concurrent-start
dedup. My own curl pass added the end-to-end proof the unit tests can't give on their own: a real
API response for a demo order id, fetched from the real company's authenticated session, returns
`404 NOT_FOUND` — never `FORBIDDEN`, satisfying the "never reveal a row exists" rule. No new RLS
mechanism was introduced (correctly — a demo company is an ordinary `company_id`-partitioned row),
and `companies` itself carries no RLS by design (pre-existing, documented at
`db/schema/tenancy.ts:27`: auth runs before the tenant is known), which is why
`isDemoCompany()`'s unscoped `db` read is correct and not a tenancy violation.

## Blocking findings
None.

## Checks
- [x] Tenancy (`withTenant`, RLS on new tables) — no new tenant tables; `companies.demoOwnerUserId`
  is a plain column + unique FK, correctly outside RLS (companies isn't a tenant table).
- [x] New `withSystem` has a reason comment — yes, see question 4.
- [x] Idempotency — demo start/reset are effectively idempotent per user (unique constraint +
  in-process dedup); webhooks/payments/labels untouched by this card.
- [x] No PII newly exposed — sample-shop buyer data is synthetic (seed builder), and the demo's
  vendor email is a `.invalid` address that can never be delivered.
- [x] Decisions recorded — report discloses the `companies.demo` keying choice and the unblocked
  money/email paths; see my rulings above for what still needs an owner-inbox entry.

## Optional notes (not blocking)
- `vendors/service.ts:232`'s `deliverInviteMail` (vendor invites) not carrying `demo` is the same
  class of gap as the label-buy/checkout one — bundle it into the same follow-up card rather than
  filing separately.
