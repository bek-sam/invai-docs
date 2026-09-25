# Wave 5 plan review — product-manager, round 1

Reviewing `invai-docs/waves/5/wave.md` and its 4 cards against `product/scope.md` and the decisions.

## Verdict: **approve with clarifications** (applied to the cards and `wave.md`)

## Scope traceability
All 4 cards trace to MVP-in items already accepted: T-5-1 → items 1, 7 (Order Hub, shipping); T-5-2 → items 2, 7 (import/channels, shipping); T-5-3 → item 14 (Today, onboarding, demo mode); T-5-4 → items 5, 14 (production floor staffing, onboarding). Every card also cites a `build/audit-2026-09-24.md` finding and/or a backlog id, and I cross-checked each against `waves/backlog.md` (B-84, B-85/90/67, B-91/72, B-92 all match the card content). Nothing here is net-new scope — it's finishing what the audit found half-built. No `scope-change-request` needed.

One correction folded into T-5-1: its evidence cited B-62 ("cancel after label") as an open backend gap. It's resolved — wave 2's T-2-5 landed it. The only real remaining piece is the web void-confirm dialog, which is T-5-2's job. I've updated T-5-1's evidence note so its scope doesn't quietly grow into re-verifying backend work that's already shipped and reviewed.

## Testable acceptance criteria
Mostly good — Given/When/Then is implicit but each bullet is a checkable behavior with a clear pass/fail (tab counts, specific stat-card links, specific confirmation dialogs). Two gaps I pushed back into the cards via the architect's contract-stub section:
- T-5-1 AC3 said `updateAddress` "re-checks the address" without saying what kind of check. That's untestable as written — a QA engineer can't tell if a carrier-level check is expected. The codebase has no such thing pre-pack (the only carrier-verified check, `shipping.rates`, requires the order already packed). I had this narrowed to an explicit, testable claim: format-only (non-empty street, valid zip), no carrier call, and the UI copy must not imply otherwise.
- T-5-3 AC1's "11 steps" count is right (5 existing + 6 new), but "computed from real data" for `carrier`, `designsUploaded`, `costsSet` and `planChosen` needs a one-line definition each so QA can write the acceptance test before the build starts (`acceptance-tests-first`). I added the concrete data source for each in `wave.md`'s contract-stub section — the card should point there.

## Demo-mode design: is a separate demo company per user right for self-serve small shops?
Yes, with one clarification I added. Reasoning:
- It reuses the platform's existing isolation primitive (`company_id` + RLS) instead of inventing a second one (e.g., seeding fake data into the real company and later "clearing" it, which risks contaminating the real onboarding checklist and billing usage, and is much harder to undo cleanly).
- It matches the existing org-switcher UX (`me.switchOrg`, `Me.orgs`) that vendor multi-org users already use — no new interaction pattern for staff to learn.
- Self-serve small shops are exactly `scope.md`'s target for this: "must self-serve without a call." A same-mechanism, low-risk sandbox is the right shape for that segment; assisted/white-glove segments get a human on the call instead and don't need this as much.
- The gap in the original one-liner: "a separate demo company for the user" doesn't say what happens when a user belongs to more than one real company (vendor + shop, or two pilots), or when they revisit demo mode later — is it a new company each time, or the same one reused? I resolved this as **one demo company per Better Auth user** (a new `companies.demoOwnerUserId` unique column), independent of which real org they're currently in, and had the architect thread that through `start`/`reset`/`leave`. Without pinning this down, "start" is ambiguous about whether it's idempotent, and QA can't write a real acceptance test for "reset."
- The bigger risk isn't the isolation model, it's that `companies.demo` is currently a decorative column — nothing excludes a demo company from the trial-expiry job or from a real marketplace OAuth flow once real keys exist. That's an architecture finding (see the architect's review), but it's also a product risk: a demo that silently breaks after 14 days, or that could theoretically hit a real Shopify store, is a support and trust problem, not just a bug. I want this treated as blocking for T-5-3, not a nice-to-have.

## PIN-only staff
Correctly scoped to `FLOOR_ROLES` (`presser`, `packer`, `receiver` — confirmed against `roles.ts`), matching who actually logs in on a floor tablet. This is real, evidenced need: office/designer/admin/owner all need email for web sign-in and notifications; floor staff don't use the web at all. No scope concern here. The one thing I flagged back to the card: the original phrasing ("no email") reads as if the backend can literally omit the field. It can't (Better Auth + the `users` table both require it) — the card should read as "the shop never provides or sees an email for this person," which is what the revised card and contract stub now say. That's a product-facing distinction worth getting right in the UI copy too: don't show an email field at all for `pinOnly` invites, not a grayed-out synthetic one.

## Changes applied
- `wave.md`: added the "Contract stubs (exact)" section (with the architect) and a "Clarifications from the plan review" note.
- T-5-1: corrected the B-62 evidence note; tightened AC3 to format-only address validation.
- T-5-3: tightened AC1's data sources; clarified demo-per-user semantics and made billing/marketplace/mail exclusion an explicit, non-optional requirement.
- T-5-4: clarified PIN-only means "no email is ever asked for or shown," not a literal null.

No owner escalation needed — nothing here changes price, plan limits, or scope beyond what's already in `scope.md`.
