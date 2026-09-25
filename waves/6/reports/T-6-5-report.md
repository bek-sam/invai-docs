# T-6-5 report: sample workspaces can never spend real money (B-109)

Status: **built, verified, ready for review** (security-reviewer).

## Commits
- contracts `1b72441`: `Org.printsInHouse` plus `me.updateOrg` `printsInHouse` (stub 2, landed early for T-6-2).
- backend `e14240a`: `printsInHouse` in `CompanySettings`, read by `toOrg`, jsonb-merged by `updateOrg`, with a test.
- web `4c19a20`: the `is-own-demo` test fixture gains `printsInHouse`.
- contracts `3b8f390`: a `DEMO_MODE` (403) common error.
- backend `5339a57`: the guard (details below).
- web `d0d89ce`: `demo.cantPay` in en and es, plus `features/demo/demo-mode.ts` (`isDemoModeError`, `demoModeMessage`).

## What counts as a sample workspace
`modules/tenancy/demo-flag.ts` has `isSampleWorkspace(companyId)`. A company is a sample workspace when `demoOwnerUserId IS NOT NULL`, **or** when it is a retired demo (`settings.demoRetiredAt`).
- **Why a retired demo counts:** reset and failed fills null the owner link. Without the marker, a retired sample company would count as a real company, and its leftover jobs (tracking polls, syncs) would go live. `retireDemoCompany` now writes the marker.
- **`companies.demo` no longer decides anything money-related.** The seeded Desert Bloom (`demo = true`, no owner) is a real shop: it gets a trial from the org hook, plan limits, `expireTrials`, invite and vendor email, and live adapters when keys are set.
- **Caching:** results are cached per process (bounded map). Status never flips, because a real company is never linked to a demo owner and a retired demo keeps its marker.
- **Helpers:** `isSampleRow` (a row already in hand), `realCompanySql()` (cross-tenant sweeps) and `demoMode()` / `assertNotSampleWorkspace()`.

## The guard: inside every factory, which now requires the company
| Factory | New signature | Sample workspace gets |
|---|---|---|
| `carrierAdapter` / `carrierTracking` | `(scope) => Promise` | mock carrier and mock tracking |
| `getChannelAdapter` | `(kind, provider, scope) => Promise` | mock, whatever the connection's stored `provider` says |
| `billingProvider` | `(scope) => Promise` | mock |
| `getSupplierAdapter` | `(supplier, creds, { companyId, production? }) => Promise` | mock supplier, even with its own S&S keys and in production |
| `sendMail` | `(mail, sender)`, where sender is `{ companyId }` or `"account"` | nothing sent (`skipped:sample-workspace`) |

- **Channel metadata:** `channelPendingApproval()` is a sync, metadata-only helper for the `.pendingApproval` reads.
- **Webhooks:** `webhookAdapter()` is now typed verify/parse only. The webhook fetch-by-id goes through `getChannelAdapter` for the matched connection.
- **Supplier display:** `supplierProvider` gains a `sample` flag, so the supplier list shows `mock`.

Because the scope argument is required, TypeScript checks every call site.

**Call sites changed** (each only to pass the company):
- `shipping/service.ts`: settings, rate, buy, void, `isMockCarrier`
- `shipping/jobs.ts`: scheduleMockTracking, pollTracker
- `channels/service.ts`: toConnection, disconnect, webhook health, pushTracking
- `channels/sync.ts`: sync, auto-import filter, webhook fetchOrder, OAuth `ensureWebhooks`
- `inventory/availability.ts`: 2 sites
- `ai/service.ts:732`: listings publish
- `inventory/service.ts`: `supplierAdapterFor`, `listSuppliers`, `supplierStock` (3 small hunks, staged apart from T-6-1's work)
- `vendors/service.ts`: sheet delivery and the known-vendor invite mail

**Extra guards:**
- The Shopify OAuth callback won't exchange a code for a sample workspace.
- Shopify connect uses `isSampleWorkspace`; the `isDemoCompany` name is removed.
- The known-vendor invite mail (`vendors/service.ts`) used to skip the demo check entirely. It now passes the company.

**Billing:**
- `checkout`, `portal` and `requestPlanChange` throw `DEMO_MODE` in a sample workspace, with a friendly message for each.
- `hasPlan`, `expireTrials` and the org hook use the sample rule.

**Auth notices (decision):** verify-email, password-reset and security notices are sent as `"account"` mail and **always go out**.
- They are about the person, not a company.
- Better Auth's hooks only know the user.
- A sample-workspace user always has a real company, because `demo.start` refuses without one.
- Gating them would break password reset for real users.

## Verification
- **Tests with fake real keys** (`src/modules/tenancy/demo-guards.test.ts`, 10 tests):
  - The live EasyPost, Shopify, Stripe and S&S providers and nodemailer are replaced by recording spies.
  - The env says real keys are set.
  - Sample and retired workspaces never reach a spy through the factories or the service call sites: shipping settings, `isMockCarrier`, a Shopify order sync of a live-marked connection, checkout/portal/plan (`DEMO_MODE`), `supplierAdapterFor`/`listSuppliers`/stock, invite, email/portal vendor delivery and `sendMail`.
  - The seeded-demo shape still reaches Stripe, EasyPost, Shopify and S&S, sends invite, vendor and account mail, and gets a trial and plan limits (the regression pin).
- **Full backend suite** (clean worktree at `5339a57`, test DB `invai_test_t65`): 488/492 pass.
  - The 4 failures are all `api/authz.test.ts`, which fails on `production.sheets.markPrinting` having no handler. That comes from T-6-2's uncommitted contract stubs in the shared contracts tree, not from this card.
  - Separately, `inventory/po-safety.test.ts` "commit failure … never orders twice" fails only in the shared tree, because of T-6-1's uncommitted `status: r.status` change (FYI for T-6-1).
- **tsc and biome:**
  - Clean for every file I touched.
  - Remaining backend tsc errors are other cards' in-progress stubs (inventory/production/ai/finance routers, sheets `printing`).
  - Web tsc has only T-6-2's `badges.tsx` `printing` error.
  - Contracts pass tsc, lint and tests (31).
  - Web: the `features/demo` tests pass.
- **Curl on DB copy `invai_t65_copy`** (API on :3150, `EASYPOST_API_KEY` and `STRIPE_SECRET_KEY` set to fake values so both run "live", imaging on :8150). Signed in as the Desert Bloom owner:
  - `demo.start` → Sample shop.
  - `shipping/settings` → `carrierProvider: mock`.
  - `shipping/rates` → mock rates.
  - `shipping/buy` → 200 `labeled`; the DB row has `carrier_shipment_id = shp_mock_…`.
  - `billing/checkout`, `billing/portal` and `billing/plan` → 403 `DEMO_MODE`.
  - `billing` → `paymentsEnabled: false`.
  - After `demo.leave`, Desert Bloom shows `carrierProvider: easypost`, `paymentsEnabled: true` and plan growth (the real behavior). No real provider call was made.
- **Cleanup:** API and imaging stopped, `invai_t65_copy` and `invai_test_t65` dropped, Redis DB 5 flushed, worktree removed.

## Known gaps and cross-card notes
- **Web wiring needs a grant.**
  - What's done: `DEMO_MODE` already shows the server's friendly English message through `errorMessage()`.
  - What's missing: Spanish needs one line in `invai-web/src/lib/errors.ts` (not owned by this card), inside `errorInfo`: `if (code === "DEMO_MODE") return { code, status, message: demoModeMessage(), data: e.data ?? null };` (import from `features/demo/demo-mode`).
  - Next step: the tech lead grants it or hands it to T-6-4 (billing page).
- **AI spend is not guarded.** Anthropic calls from a sample workspace (listing drafts, the assistant) still use the platform key when one is set. That is real money but outside this card's AC. Suggest a backlog item.
- **Channel token refresh** (`refreshExpiringTokens`) filters `provider = 'live'` rows and isn't sample-guarded. It spends nothing, and a sample workspace can't create a live connection (connect forces mock).
- `onboarding.ts` still reads `companies.demo` (checklist display only, not money).
