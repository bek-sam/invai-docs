# Wave 2 plan review — product-manager, round 1

## Verdict: approve (with clarifications applied to the cards)

## Scope traceability
- **T-2-1 (Stripe billing, backend)** cites `scope.md#mvp-in` item 15, "Plan limits (Stripe checkout when
  keys exist)". Decision `0006-v1-cuts.md` lists "Stripe checkout: stubbed, with plan limits enforced" —
  that's a v1 build note (what shipped Sep 23–24), not a scope cut. Item 15's own parenthetical already
  says the real checkout comes in "when keys exist," which is exactly this project's standing pattern
  (`CLAUDE.md`: "every integration has a mock provider, chosen automatically when its key is missing").
  **Judgment: T-2-1 is in scope.** It builds the live Stripe adapter behind the existing mock switch; it
  doesn't reopen decision 0006, it fulfills the part of item 15 that 0006 deferred.
- T-2-2 (billing UI) is the UI half of the same scope item 15. In scope.
- T-2-3/T-2-4 (account security) are "always-in-scope: security" per `scope.md`. In scope, and overdue —
  the audit (`audit-2026-09-24.md` B-60) already found no password reset and account menu with no
  security options.
- T-2-5 (crash-safe labels/tracking/cancel) cites scope items 1 and 7 plus "always-in-scope: bug (money)".
  Verified against code: `shipping/service.ts` really does call the carrier from inside a `withTenant`
  transaction in both `rateOrder` and `buyLabel` (row lock held via `.for("update")` in `rateOrder`), and
  `orders/service.ts:cancelOrder` really does let a `packed` item be cancelled with no label-void check.
  In scope, evidence-backed, not a "one shop's quirk."

## Acceptance criteria — testable and user-meaningful
All five cards give numbered, concrete criteria (not full Given/When/Then, but each is independently
verifiable: e.g. T-2-1 #2's webhook behavior, T-2-5 #1's "a test simulates a commit failure after the
carrier charged, and the retry doesn't charge twice"). That's appropriate for hardening/bug cards derived
from the audit rather than fresh feature specs — `scope.md`'s "always in scope" bucket (bugs, security)
doesn't require a `specs/` document, and none of these cards invent new user-facing behavior without a
verification step. No gold-plating found: each criterion maps to either an audit finding or the wave's
stated user outcome.

One gap: T-2-1's AI credit pack criterion (#7) doesn't say what happens if the webhook for a one-time
pack purchase arrives before the `checkout.session.completed` handler has resolved which company/pack it
belongs to — but this is a build-time detail the acceptance test in #9 ("each event type, replays,
out-of-order events") should catch; not blocking.

## EMAIL_NOT_VERIFIED gate on paid actions — sensible for small shops?
As originally drafted, T-2-3 gated **label buy, checkout, and connecting a channel** behind email
verification. Label buy and checkout both move real money and are reasonable to gate — an unverified
email is a common fraud/chargeback vector and neither blocks a shop from doing anything else.

**Connecting a channel is different and I changed it.** Small shops (`scope.md` segment table) must
"self-serve without a call," and connecting the first marketplace (CSV import, or Shopify OAuth) is the
very first thing a new shop does after signup — before any order has ever moved, let alone any money.
Gating it on email verification means a transactional-email hiccup (spam filter, SES sandbox delay,
typoed address) strands a brand-new self-serve shop before it has seen any value. It also doesn't reduce
fraud risk in a way label-buy/checkout gating doesn't already cover, since connecting a channel by itself
doesn't spend money. **Applied:** removed "connecting a channel" from T-2-3's acceptance criterion 1; the
gate now covers only label buy and `billing.checkout`/`billing.portal`.

## Trial-expired behavior
`trial_expired` blocking imports and label buys with `PAYMENT_REQUIRED` while "reading data still works"
is the right shape — a shop that stops paying shouldn't be able to bring in new work or spend money, but
shouldn't lose visibility into what it already has. The original wording left one thing unclear: whether
orders already in the system can still move through the production floor (pick/press/QC/pack/scan) once
a company is `trial_expired`. Floor work doesn't spend money and stopping it mid-order would strand
physical goods and hurt the shop far more than it protects the business. **Applied:** clarified T-2-1
acceptance criterion 5 to state explicitly that floor operations keep working; only imports and label
buys are gated.

## Changes made
- `invai-docs/waves/2/T-2-3-account-security-backend.md`: acceptance criterion 1 — removed "connecting a
  channel" from the `EMAIL_NOT_VERIFIED` gate, with the self-serve-onboarding reasoning inline.
- `invai-docs/waves/2/T-2-1-stripe-billing.md`: acceptance criterion 5 — clarified that `trial_expired`
  doesn't stop in-flight orders moving through the production floor.

## Not required, but noted
- The pricing hypothesis (`scope.md`) is still unresolved for the small-shop entry plan ($49–149/mo vs.
  the $149/$349/$699 catalog `billing/service.ts` currently ships). T-2-1 explicitly keeps "the current
  catalog" and treats pricing as out of scope (OI-1), which is correct — not this wave's problem to solve,
  but flagging so it isn't forgotten before public launch.
