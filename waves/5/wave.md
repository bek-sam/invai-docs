# Wave 5: office web, orders and settings

- Goal (user outcome):
  - The office can run a day from the web app. On each order they can set rush, flags and tags, see the shipment, and fix a held address.
  - They can connect channels, set up shipping, onboard step by step, try a demo, and manage the team and tablets.
  - No dead ends.
- Plan reviewed by: product-manager (`reviews/plan-product-manager-r1.md`), architect (`reviews/plan-architect-r1.md`)

## Cards
| Card | Owner | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|
| T-5-1 Order detail actions and shipment section | web-engineer (+ backend-engineer orders for the address edit) | reviewer + product-designer, architect | ui | planned |
| T-5-2 Channels and shipping settings | web-engineer | reviewer + product-designer | ui | planned |
| T-5-3 Onboarding, Today and demo mode | backend-foundation + web-engineer | reviewer + product-designer, security-reviewer | ui, tenancy | planned |
| T-5-4 Team and stations | web-engineer (+ backend-foundation for PIN-only staff) | reviewer + product-designer, security-reviewer | ui, auth | planned |

Only 3 builders at once: T-5-1, T-5-2 and T-5-3 first, then T-5-4.

## Agreed interfaces (architect commits the stubs first; the exact shapes are written by the plan review)
- `orders.updateAddress({ orderId, address })`: allowed only while the order is held for `address_check` or not yet labeled (no shipment in a `LIVE_LABEL` state). It runs a format-only address check (no carrier call — the only carrier-verified check, `shipping.rates`, needs a packed order) and releases the hold when the address passes.
- `OnboardingChecklist` gains: `shipFromAddress`, `carrier`, `tabletPaired`, `designsUploaded`, `costsSet`, `planChosen`, `dismissed`, `dismissedAt`. Plus `today.dismissChecklist()`.
- Demo: `tenancy.demo.start()` creates or refreshes a sample-data workspace for the user, `tenancy.demo.reset()` and `tenancy.demo.leave()`. The demo company is flagged `demo=true`, is isolated by RLS (free — it's an ordinary `company_id`-partitioned row like any other), and is excluded from billing, marketplace calls and mail (not free — see "Contract stubs (exact)" below; none of this exists today).
- `team.invite` accepts `{ name, role, pinOnly: true }` with no email, for floor roles. That creates a PIN-only member who can't sign in on the web. **Revised in review:** Better Auth's own `user` schema hard-requires a unique, non-null `email` (`@better-auth/core`'s `get-tables.mjs`), and so does the `users` table itself (`NOT NULL UNIQUE`, `db/schema/tenancy.ts:35`) — the same table Better Auth writes to. `email` cannot become genuinely absent. See the exact shape below: `email` stays required in the schema (backend fills a synthetic, non-deliverable placeholder), and a new `pinOnly` flag tells the web (and the mailer) never to treat it as a real address.

## Contract stubs (exact)
Committed by the architect first; consumers build against these shapes, not the summary above. All changes are additive (new optional fields, new enum values appended, new procedures) per the contract rule in `CLAUDE.md`/`architect.md` — nothing existing is renamed or removed.

### 1. `orders.updateAddress` (T-5-1)
```ts
// contract/orders.ts
updateAddress: proc("orders.manage")
  .route({ method: "PATCH", path: "/{id}/address" })
  .input(z.object({ id: Id, address: Address }))
  .output(OrderWithItems)
  .errors({
    ADDRESS_LOCKED: {
      status: 409,
      message: "This order already has a shipping label; void it first",
    },
  }),
```
```ts
// schemas/orders.ts — TIMELINE_KINDS gains one entry, appended at the end (additive)
export const TIMELINE_KINDS = [
  "imported", "state_changed", "mapped", "artwork", "flag", "held", "released",
  "cancelled", "scan", "sheet", "qc", "reprint", "shipment", "tracking_pushed",
  "note", "sync",
  "address_updated", // NEW
] as const;
```
Backend (`modules/orders/service.ts`, new `updateAddress` next to `holdOrder`/`releaseOrder`):
- **Gate:** refuse `ADDRESS_LOCKED` if any shipment for the order has `status` in `LIVE_LABEL` — the exact set `shipping/service.ts:79` already uses (`["labeled","in_transit","delivered","exception","returned"]`), queried the same way `shipping/service.ts:1006-1008` does. Don't gate on `orders.status`; it's a derived rollup, not the source of truth for "has a live label."
- **Validation:** format-only, reusing the identical heuristic already at `shipping/service.ts:482` (non-empty `street1`, zip matches `/^\d{5}(-\d{4})?$/`). Reject with a plain `INVALID_TRANSITION`-style 422 (reuse `ADDRESS_INVALID`'s shape from `contract/shipping.ts` — same message/data contract, just a new instance in `orders`) if it fails. There is no carrier-verified check available pre-pack; don't imply one in the UI copy.
- **Persistence:** upsert `buyerPii` exactly like `orders/import.ts:283-360` (`piiValues` + the `updateExisting` address branch) — insert if no row exists, update if street1/street2/city/state/zip/name differ from what's stored.
- **Hold interaction:** if `order.holdReason === "address_check"`, call the existing `releaseOrder` transition path once the write succeeds. Otherwise, just write the address and add a `TimelineEntry` (`kind: "address_updated"`) — no state change. This covers the "not yet labeled" case (a pre-production typo fix with no hold in play).
- **Permission:** `orders.manage`, matching the `canSeeAddress` gate already used when reading `shipTo` (`orders/service.ts:136`).

### 2. `OnboardingChecklist` + `today.dismissChecklist` (T-5-3)
```ts
// schemas/tenancy.ts
export const OnboardingChecklist = z.object({
  channelConnected: z.boolean(),
  blanksImported: z.boolean(),
  skusMapped: z.boolean(),
  vendorAdded: z.boolean(),
  staffInvited: z.boolean(),
  shipFromAddress: z.boolean(),   // NEW: Location.address or ShippingSettings.fromAddress set
  carrier: z.boolean(),           // NEW: ShippingSettings.allowedCarriers non-empty
  tabletPaired: z.boolean(),      // NEW: any StationDevice has tokenIssuedAt set
  designsUploaded: z.boolean(),   // NEW: catalog designs count > 0
  costsSet: z.boolean(),          // NEW: any blank/design cost record set (settings/costs.tsx's data)
  planChosen: z.boolean(),        // NEW: subscription.status !== "trialing", or a plan was explicitly picked
  dismissed: z.boolean(),         // NEW
  dismissedAt: Timestamp.nullable(), // NEW
});
```
```ts
// contract/today.ts — additive
dismissChecklist: proc("today.read")
  .route({ method: "POST", path: "/onboarding/dismiss" })
  .input(z.object({ dismissed: z.boolean().default(true) }))
  .output(OnboardingChecklist),
```
**Ownership correction:** the checklist is not in `modules/today/**` today — it's `onboarding()` in `modules/tenancy/service.ts:92-105`, called from `me()` (`service.ts:108-133`). T-5-3's owned-paths list needs `modules/tenancy/service.ts` added (or, cleaner, extract `onboarding()` into a new `modules/tenancy/onboarding.ts` that both `me()` and a thin `today.dismissChecklist` handler call) — as written the card grants no path that reaches the code it needs to change. `dismissed`/`dismissedAt` persist in `company_settings` (`db/schema/tenancy.ts:67-71` already holds a small per-company settings block) as a new key, not a new table.

### 3. `tenancy.demo.{start,reset,leave}` (T-5-3)
```ts
// contract/tenancy.ts (or a small new contract/demo.ts under the tenancy tag)
export const demo = base
  .prefix("/tenancy/demo")
  .tag("tenancy")
  .router({
    start: proc("none").route({ method: "POST", path: "/start" }).input(z.object({})).output(Me),
    reset: proc("none").route({ method: "POST", path: "/reset" }).input(z.object({})).output(Me),
    leave: proc("none").route({ method: "POST", path: "/leave" }).input(z.object({})).output(Me),
  });
```
All three return `Me` — the same shape `me.switchOrg` returns — so the web client updates its session context in one call instead of a call-then-refetch.
- **One demo company per user, not per real company.** Add `companies.demoOwnerUserId: uuid().unique().nullable()` (new column + migration) so `start()` can find "this user's demo company" regardless of which real org they clicked from. `start()` finds-or-creates-then-seeds; `reset()` wipes and reseeds the company found by `demoOwnerUserId`; `leave()` switches back to the user's primary org without deleting the demo company.
- **Billing exclusion is genuinely new work, not a flag check.** `companies.demo` (`db/schema/tenancy.ts:62`) exists but is read nowhere except `toOrg()` (`service.ts:52`) — confirmed zero other usages in `src/`. Concretely:
  - `today/org-hooks.ts:16-41` (`onOrganizationCreated`, the generic Better Auth `organization.create` hook, wired at `auth.ts:340`) unconditionally inserts a 14-day trial `subscriptions` row for every shop-type org, demo included. `billing/service.ts`'s `expireTrials()` job is a bulk `UPDATE ... WHERE status='trialing' AND trialEndsAt<=now` with no company filter, so an unpatched demo company's trial silently expires after two weeks and locks the demo. Fix: skip the `subscriptions` insert for a demo company (or make `expireTrials`/`assertWithinPlan` demo-aware).
  - `assertWithinPlan` (`billing/service.ts:569`, called from `channels.connect` and `team.invite`) must short-circuit for `company.demo === true` once the subscription insert is skipped.
- **Marketplace-call exclusion is also genuinely new work.** `channels/service.ts:366`: `const provider = env.mocks.shopify ? "mock" : "live"` — a pure env-level decision with no per-company check. In a deployment with real keys, a demo company connecting Shopify would run a real OAuth flow against a real store. This must force `"mock"` whenever `company.demo === true`, independent of `env.mocks`; check every other `env.mocks.*` branch (vendors, other channels), not just Shopify's.
- **Mail exclusion:** any transactional email (invite, password reset) must no-op for `demo === true`, same reasoning as the PIN-only placeholder email below.
- **RLS isolation needs no new mechanism** — it's an ordinary `company_id`-partitioned row like any other company; the security-reviewer co-review should confirm with the normal `tenant-isolation-audit`, not a bespoke demo check.

### 4. `team.invite` with `pinOnly` (T-5-4)
```ts
// schemas/tenancy.ts — additive: User gains pinOnly
export const User = z.object({
  id: Id,
  email: z.email(),          // unchanged: still always a real (possibly synthetic) string
  name: z.string(),
  role: RoleSchema,
  status: z.enum(USER_STATUSES),
  hasPin: z.boolean(),
  pinOnly: z.boolean().default(false), // NEW
  lastSeenAt: Timestamp.nullable(),
  createdAt: Timestamp,
});
```
```ts
// contract/tenancy.ts — team.invite input replaced with a refined union-by-flag (additive: email
// only becomes optional, nothing existing is removed or renamed)
invite: proc("team.manage")
  .route({ method: "POST", path: "/invite" })
  .input(
    z.object({
      name: z.string().min(1),
      role: z.enum(ROLES),
      email: z.email().optional(),
      pinOnly: z.boolean().default(false),
    })
      .refine((v) => v.pinOnly || !!v.email, { message: "email is required unless pinOnly", path: ["email"] })
      .refine((v) => !v.pinOnly || (FLOOR_ROLES as readonly string[]).includes(v.role), {
        message: "pinOnly staff must be a floor role (presser, packer or receiver)",
        path: ["role"],
      }),
  )
  .output(User),
```
Backend (`modules/tenancy/service.ts`, new branch in `inviteUser`/`inviteTeammate`, `service.ts:268-336`):
- **Why `email` stays required in the schema:** confirmed in `node_modules` — `@better-auth/core`'s base `user` table defines `email: { type: "string", unique: true, required: true }` with no supported override, and `db/schema/tenancy.ts:35`'s `users.email` is a real Postgres `NOT NULL UNIQUE` column — the *same table* Better Auth's adapter writes to (`auth.ts`'s `drizzleAdapter` schema config passes InvAI's own `users`/`members` tables directly). A genuinely-null email is not achievable without forking Better Auth. `staff_pins.userId` also has a `NOT NULL` FK to `users.id` (`tenancy.ts:277-279`), so PIN-only staff must be a real `users` row.
- **What `pinOnly: true` actually does:** insert a `users` row directly via Drizzle (bypassing `auth.api.signUpEmail`, which wants a password and sends a verification email) with a synthetic, non-deliverable placeholder like `pin+<uuid>@floor.invai.internal`; no `accounts` row (no password exists, so there's nothing to sign in with on the web); an active `members` row with the chosen floor role; then the normal `setPin` flow for the `staff_pins` row.
- **Guardrails to add, not optional:** the mailer (`integrations/vendors/mailer.ts`) and any future notification/reset-password code must treat `pinOnly` (or the `@floor.invai.internal` suffix) as "never send here." The web must gate every place it renders or edits `email` on `!user.pinOnly` — never show the placeholder as if it were a real contact address.
- **Invitation uniqueness (also new):** `invitations` (`tenancy.ts:177-193`) has only plain, non-unique indexes on `organizationId` and `email` today; dedup is app-level only (`cancelPendingInvitations`, `invites.ts:174-191`, called from `service.ts:289` — not atomic, and gives the UI no "an earlier invite is pending" signal). T-5-4 needs a real `uniqueIndex().on(organizationId, email).where(status = 'pending')` (partial unique index) plus a `resend`/`revoke` pair in `contract/tenancy.ts`'s `team` router (neither exists today).
- **Last-owner-deactivate guard:** `changeRole` already refuses demoting the last owner (`activeOwnerCount()`, `service.ts:204-216`, checked at `service.ts:376-377`). No equivalent guard was found on the deactivate path — verify and add one; don't assume it's covered.

## Parallel work rules
The same as `waves/3/wave.md`, "Parallel work rules". Numbers per card:
- Test DB `invai_test_t5<k>`.
- API port `31<k>0`, web dev server `51<k>3`.
- `REDIS_URL=redis://localhost:6379/<k>`.
- DB copy `invai_t5<k>_copy` (then `db:migrate`).

Web file ownership, since four cards share invai-web:
- **T-5-1:** `features/orders/**`, `routes/_app/orders/**`.
- **T-5-2:** `routes/_app/settings/{channels,shipping}.tsx`, `routes/_app/shipping.tsx` (the void confirm only).
- **T-5-3:** `routes/_app/index.tsx` (Today), new `features/demo/**` and `features/onboarding/**`, the demo badge in `app-frame.tsx`.
- **T-5-4:** `routes/_app/settings/{team,stations}.tsx`.
- **i18n:** each card adds its own keys by hand and commits only its own hunks. Never run `pnpm i18n`.

## Clarifications from the plan review (applied here and to the cards)
- T-5-1's evidence cited B-62 ("cancel after label") as open; it's resolved (wave 2, T-2-5). The real remaining gap T-5-1/T-5-2 inherit is the **web-side void confirmation dialog** only (B-67's web half) — see T-2-5's report for the exact reject/retry/refund-pending states the confirm copy needs to cover.
- T-5-3's owned paths must add `invai-backend modules/tenancy/service.ts` (or a new `modules/tenancy/onboarding.ts` it and T-5-3 both touch) — the checklist doesn't live in `modules/today/**`.
- T-5-4's owned paths must add the `invitations` table's migration (a new partial unique index) — already implied by "the invitation unique index migration" in the card, now confirmed as net-new (no such index exists).

## Integration gate
- [ ] `df -h /` above 5 GB
- [ ] Fresh reset, migrate, seed
- [ ] API, browser and floor E2E pass
- [ ] Builds pass
- [ ] Per-card DBs and worktrees removed
- [ ] Pushed to `main`
