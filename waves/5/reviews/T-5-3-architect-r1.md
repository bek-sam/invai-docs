# Review of T-5-3 (round 1) — architect co-review

- Reviewer: architect on Sonnet 5
- Author: backend-foundation + web-engineer on Opus 5.5 (contract stubs: architect on a prior turn, `2f84ae6`/`352c331`/`796ba2c`)
- Verdict: approve

Scope: the contract stubs (mine to answer for, since I also authored them) and this card's build
against them — additivity, the permission model, and the cross-module shape of the seed builder
and the demo/onboarding split. Tenancy proof and UI are the security-reviewer's and
product-designer's files.

## Evidence I re-ran
| Command | Result |
|---|---|
| `invai-contracts` @ `352c331` (already `main`'s tip): `tsc --noEmit` / `vitest run` | clean / 4 files, 31 passed, incl. `contract.test.ts`'s exact-five `"none"`-permission allowlist and the "known permission" check |
| `git diff 6718f56 2f84ae6 -- src/contract src/schemas` | additive only: new optional/appended fields, new procedures, no renamed or removed exports (see Checks) |
| `git diff 2f84ae6 352c331 -- src/contract/tenancy.ts` | the one substantive change between the two stub commits: `demo.{start,reset,leave}`'s permission, `org.read` → `today.read` |
| `grep -n "\"none\"" invai-contracts/src/contract/*.ts` | 5 procedures (`floor.login`, `floor.logout`, `floor.staff`, `me.get`, `me.switchOrg`) — matches `contract.test.ts`'s allowlist; `demo.*` correctly does **not** appear |
| `invai-backend` worktree @ `72c1139`: read `modules/tenancy/onboarding.ts`, `demo.ts`, `demo-flag.ts`, `db/seed/builder.ts`'s `backdateTimelines` | see notes below |

## Ruling on question 7 (the stubs: additive, `today.read` for demo)

**Additivity — confirmed clean.** `2f84ae6`'s diff to `src/contract` and `src/schemas` is entirely
new optional fields on `OnboardingChecklist` (six, all with inline comments naming their source),
one appended `TIMELINE_KINDS` entry, and new procedures/routers (`orders.updateAddress`,
`today.dismissChecklist`, the `demo` router, `team.resend`/`revoke`). `User.email` picked up a
clarifying comment only, not a type change. Nothing existing was renamed, removed, or had its
required-ness tightened — matches `CLAUDE.md`'s contract rule and the wave doc's own "additive
only" framing.

**The `today.read` permission fix (`2f84ae6` → `352c331`) is the right call, and I'd have made the
same one.** The first stub commit used `org.read` for `demo.*`, reasoning it gave "any signed-in
user" reach without needing a new permission or violating the `"none"`-allowlist invariant
(`contract.test.ts`'s exact five). That reasoning about the allowlist was correct, but the specific
permission was wrong: `org.read` is held by the vendor role too (confirmed:
`ROLE_PERMISSIONS.vendor` includes `org.read`), so a vendor org could have reached
`tenancy.demo.start` and ended up owning a shop-shaped sample company — meaningless at best,
a data-model violation at worst (a vendor-type user with a `demo=true` shop-type company via
`demoOwnerUserId`, something `startDemo`'s own `orgType === "vendor"` guard has to defensively
reject at the service layer because the permission layer let it through). `authz.test.ts`'s
"vendor users hold only vendor-portal and own-org permissions" test caught this, which is exactly
what that test is for. `today.read` is the correct fix: every shop role holds it, no vendor role
does, and it needed no new permission or `ROLE_PERMISSIONS` change. I re-ran `contract.test.ts`
and confirmed `demo.*` isn't in the `"none"` allowlist and does resolve to a known permission.

**One design note, not a blocker:** `demo.*` being gated on `today.read` rather than a bespoke
`demo.manage` permission means any future role that needs `today.read` for an unrelated reason
automatically gets demo access too. That's fine today (every shop role should have both), but if a
future card ever wants a shop role that can see Today without being able to spin up sample
workspaces (unlikely, but not unthinkable — e.g. a read-only "accountant" role), this coupling
would need revisiting. Worth a one-line note in `contract/tenancy.ts`'s existing comment for the
next architect who touches roles, not a blocker for this round.

## Architecture of the demo/onboarding split
`onboarding.ts` (the checklist) and `demo.ts` (the sample workspace) are cleanly separated:
`onboarding.ts` is a pure read (plus one settings-key write) with no side effects beyond what's
already true of the shop; `demo.ts` owns the one place that creates, fills, and retires whole
companies. `demo-flag.ts`'s `isDemoCompany()` is a small, single-purpose helper reused by
`channels/service.ts` — the right shape for a cross-module check (a shared predicate, not a
`companies.demo` read duplicated at each call site). This mirrors the pattern the card asked for
("check every other `env.mocks.*` branch") without spreading `companies` queries around.

The seed builder extraction (`db/seed/index.ts` → `db/seed/builder.ts`) is a reasonable
architectural move for the stated purpose (one shop-data builder for both `db:seed` and
`tenancy.demo`), parameterized correctly on the things that actually differ between a full seed
and a demo (company, PRNG, transaction runner, people, volumes, renders) rather than branching
internally on "is this a demo." The size (about 1,500 moved lines) was flagged and accepted in the
plan review as this card's own scope, not creep, and I agree with that call — a smaller extraction
that left `db:seed` calling into two different code paths for "the same" shop-generation logic
would have been the worse architecture, not the better one.

## Ruling on question 4 (`withSystem` for backdating) — architecture angle
Security-reviewer's file covers the tenancy/safety verdict (justified, narrowly scoped, tested).
From an architecture standpoint: this is the same pattern the full seed has always used for the
identical reason (`order_item_transitions` is append-only for the app role), applied consistently
rather than inventing a second mechanism for the demo path. I'd flag it if `demo.ts` had grown its
own bespoke backdating logic outside `builder.ts`; it didn't — `fillDemoCompany` calls the same
`buildShopData`/`backdateTimelines` the seed does, with `runHistory` as an injected function rather
than a hardcoded `withSystem` call inside the demo module itself. That's the correct level of
indirection: the append-only-trigger workaround lives in one place (`builder.ts`), not two.

## Ruling on question 5 (slug detection) — contract angle
I agree with the report's own follow-up and with product-designer's ruling: this should become an
explicit field on `Org` (e.g. `Org.demoOwned: boolean`, computed server-side as
`companies.demoOwnerUserId === session.userId`) rather than a string-convention the web has to
reverse-engineer from `slug`. It's additive, low-risk, and removes a documented "known gap" from
the report. **I'm noting this as a recommended follow-up for the next card that touches
`contract/tenancy.ts`'s `Org` schema, not a blocker for this round** — the current slug convention
is pinned by a real test (`is-own-demo.test.ts`) and has no security implication (the backend's
`demoOwnerUserId` lookup is authoritative for every actual demo operation), so blocking this card
to add one contract field would be scope creep in the other direction.

## Blocking findings
None.

## Checks
- [x] Contract changes additive — confirmed above.
- [x] Cross-module work reviewed — `billing/service.ts`, `channels/service.ts`,
  `today/org-hooks.ts` grants were narrow and match exactly what the wave doc specified (the demo
  checks only, nothing wider).
- [x] Decisions recorded — the report's decisions on keying on `companies.demo`, retire-not-delete,
  the one `withSystem`, in-request fill, and the two checklist-field definitions are all
  consistent with what the contract and wave doc actually specify.

## Optional notes (not blocking)
- `Alert.data` (for full alert-detail translation) and `Org.demoOwned` (for the slug-detection
  follow-up) are both small, additive contract asks from this card's known gaps — worth batching
  into one future architect-authored stub commit rather than two, since neither depends on the
  other.
