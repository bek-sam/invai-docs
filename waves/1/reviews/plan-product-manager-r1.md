# Product-manager review of the Wave 1 plan (round 1)

- Reviewer: product-manager
- Author: tech-lead
- Verdict: **approve** — one clarifying change applied (below); every card traces to scope and the acceptance criteria are testable and user-meaningful.

## What I checked
`scope.md`, `roadmap.md`, `audit-2026-09-24.md`, `wave.md`, and each `T-1-*.md` card's scope ref, acceptance criteria and out-of-scope section, against: does it trace to `scope.md` or "always in scope," are the ACs testable and meaningful to a user/owner (not just an engineering nicety), and is anything outside scope smuggled in.

## Scope traceability
| Card | Ref | Traces? |
|---|---|---|
| T-1-1 | always-in-scope: bug (B-56 broken build) / security (B-50 prod mock guard) | Yes — a broken `pnpm build` blocks everything, and a mock-fed production is a straightforward security/trust finding. |
| T-1-2 | always-in-scope: security | Yes — unverified/unsigned webhooks writing to the DB is a textbook security finding, and `operating-system.md` rule 8 requires webhook idempotency outright. |
| T-1-3 | always-in-scope: security (money); `scope.md#mvp-in` item 6 (blank inventory, POs, receiving) | Yes, doubly — a tenant able to spend against InvAI's own supplier account is a real money/security incident waiting to happen, and PO submit/receive is explicitly item 6. |
| T-1-4 | `scope.md#mvp-in` items 9, 14 (bug) | Traces via "bug in a shipped feature" (invites are advertised but don't work: no email, no working accept link) — always in scope regardless of the item numbers cited. The item-9/14 references are loose (invites aren't their own numbered line item); not blocking, since the bug framing alone is sufficient, but see note below. |
| T-1-5 | `scope.md#mvp-in` item 11 (bug, trademark check) | Yes for the trademark half. The card's AC1 also folds in the plan catalog, which `roadmap.md`'s wave-1 line already names ("B-54 reference data (trademarks, plans)"), so it's sanctioned — just not cited under item 15 (Plan limits) in the card's scope ref. Not blocking. |

Nothing in the five cards is new functionality outside `scope.md`'s MVP-in list or the always-in-scope bugs/security carve-out. Each card's "Out of scope" section correctly pushes adjacent work to later waves (supplier-settings UI to wave 6, PIN-only staff and resend/revoke UI to wave 5, Shopify polling/paid-filter/refunds to wave 3, a USPTO bulk loader to later) instead of scope-creeping into wave 1.

## Acceptance criteria: testable and user-meaningful
All five cards' criteria are stated as concrete, checkable behavior (a boot outcome, an HTTP status code, a single supplier order after two submits, a working email link, a query count on an empty DB) rather than vague goals — good, matches `write-spec`'s Given/When/Then spirit even though these are engineering cards, not specs. Each maps to something a shop owner would actually feel:
- T-1-1: the owner can safely turn on real keys without the app quietly lying about what's live.
- T-1-2: a forged webhook can't write fake orders or double-import a real one.
- T-1-3: a shop can't accidentally (or via a bug) place an order that bills InvAI's own supplier account, and a retried PO submit/receive can't double-order or double-stock.
- T-1-4: inviting a teammate or vendor actually gets them into the product — this is a top-of-funnel blocker today (B-51/B-52), and it's currently broken for every segment, small and mid alike.
- T-1-5: a fresh production database doesn't quietly approve trademark-infringing listings because the reference table is empty — directly protects item 11's promise.

## Required change (applied)
T-1-3's acceptance criteria (AC2/AC3) turn out to need a small, additive field on `invai-contracts`' `ReceiveInput` schema (a client-supplied idempotency key) that no card in this wave was scoped to add — `invai-contracts/**` is architect-owned, and wave 1 has no dedicated architect card. This is really an architecture-ownership gap rather than a scope gap (the *feature* — idempotent receiving — is squarely in scope), so I deferred the fix to the architect review (`plan-architect-r1.md`), which adds it to `wave.md`'s "Agreed interfaces" as a stub the architect commits before T-1-3's build starts, and adds architect as a required co-reviewer on T-1-3. No scope change needed on my end.

## Notes (not blocking)
- T-1-4's scope ref would be cleaner as "always-in-scope: bug in a shipped feature" rather than pointing at items 9/14, which don't cleanly cover staff invites. Worth tightening next time a card cites scope items loosely, but not worth a re-review round for wording.
- T-1-5's scope ref could cite item 15 (Plan limits) alongside item 11, since AC1 explicitly covers the plan catalog too. Same — cosmetic, not blocking.
- Wave 1 rightly has no product-facing UI card; all five are trust/safety plumbing ("safe to put real keys in"). That matches the roadmap's stated wave order (P0 safety first) — I'd flag it if a wave like this shipped without a following wave that gets a pilot something new to use, but wave 2 (money and accounts) is next, so the sequencing is fine.
