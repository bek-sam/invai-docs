# T-5-3: Onboarding checklist, Today fixes, demo mode

| Field | Value |
|---|---|
| Scope ref | `product/scope.md#mvp-in` item 14 |
| Backlog | B-91, B-72 |
| Owner | backend-foundation (demo and checklist backend) + web-engineer (UI). One agent may do both, committing backend and web separately. |
| Reviewer | reviewer; co-reviewers product-designer, security-reviewer (demo isolation) |
| Risk flags | ui, tenancy |

## Owned paths
- invai-backend `modules/today/**`, `modules/tenancy/demo*.ts` (new), `modules/tenancy/service.ts` (**added in plan review** — the checklist actually lives here, in `onboarding()` at `service.ts:92-105`, not in `modules/today/**`; today's `org-hooks.ts` and `service.ts` have no checklist code at all), `modules/tenancy/onboarding.ts` if you choose to extract it, `modules/billing/service.ts` (**added in plan review**, narrow grant — only `expireTrials`/`assertWithinPlan`'s demo check) and `modules/channels/service.ts` (**added in plan review**, narrow grant — only the `provider = env.mocks.X ? "mock" : "live"` branches, to force `"mock"` for a demo company), and the seed's reusable demo-data builder (refactor the seed so demo data can be generated for any company, without breaking `db:seed`)
- invai-web `routes/_app/index.tsx`, `features/demo/**`, `features/onboarding/**`, the demo badge in `app-frame.tsx`, own i18n keys
- tests

**Clarified in plan review (architect r1):** the exact `OnboardingChecklist`/`tenancy.demo.*` contract shapes are in `wave.md` under "Contract stubs (exact)" §2–3 — read those before starting, they fix real gaps this card's original text glossed over:
- `companies.demo` (`db/schema/tenancy.ts:62`) exists but is read nowhere else in the codebase. "Excluded from billing" and "marketplace calls (mock only)" are **not** flag checks — they're new logic in `today/org-hooks.ts` (skip the trial-subscription insert), `billing/service.ts` (`expireTrials`, `assertWithinPlan`), and `channels/service.ts:366` (force `provider: "mock"` regardless of `env.mocks`, and check every other `env.mocks.*` connect path, not just Shopify's). Without this, a demo company's trial silently expires after 14 days (locking the demo) and, in a deployment with real keys, "connect Shopify" on a demo company would run a real OAuth flow.
- The seed refactor is large on its own (~2,000 lines across `db/seed/index.ts` and `data.ts`, a module-level PRNG seeded once at import time that every random call closes over, hardcoded volumes like the 300-order loop, a slug-based idempotency guard specific to Desert Bloom) — see the plan review for the full risk list. If it slips past one review round on its own evidence, split it into its own card next wave rather than trying to land it alongside the checklist/Today/demo-UI work in a second round.

## Acceptance criteria
1. **Checklist:**
   - 11 steps: the 5 existing ones plus ship-from address, carrier, tablet paired, designs uploaded, costs set, plan chosen.
   - Each step is computed from real data and links to where it's done.
   - It can be dismissed per company, and reopened from the help menu.
2. **Today:**
   - The stat cards link to the right filtered views (due today, overdue, blocked includes artwork).
   - Hint text is visible.
   - Alerts are translated from `alert.kind`.
3. **Demo mode:**
   - "Try with sample data" on an empty workspace, and from the account menu, creates a separate demo company **for the user** (one per Better Auth user — track it with a new `companies.demoOwnerUserId` unique column, so `start()`/`reset()` find the same demo company regardless of which real org the user clicked from), filled with realistic sample data from the seed builder (smaller than the full seed, for speed). It switches to it with a clear "Demo" banner and a "Leave demo" button.
   - "Reset demo" rebuilds it.
   - Demo companies are excluded from billing (no trial-expiry lockout — see "Owned paths"), emails (mailer no-ops for `demo === true`, same as the PIN-only placeholder email in T-5-4) and marketplace calls (`channels/service.ts` forces the mock provider for a demo company regardless of `env.mocks`).
   - RLS isolation is proven by a test — this part needs no new mechanism (a demo company is an ordinary `company_id`-partitioned row), the test just has to confirm no code path used `withSystem` where `withTenant` belonged.
4. **Seed:** `db:seed` still produces the same Desert Bloom data.

## Verification
- Typecheck, lint, test and build in backend and web.
- On a DB copy: sign up a new shop, see the checklist, start the demo, browse, reset, leave. Show that the demo data doesn't appear in the real company. Screenshots in en and es.
