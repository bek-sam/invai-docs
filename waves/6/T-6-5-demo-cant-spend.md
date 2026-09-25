# T-6-5: Demo workspaces can never spend real money (B-109)
Scope: always-in-scope, security and money. Model: opus.

## Owned paths
- backend: `modules/tenancy/demo*.ts`, `today/org-hooks.ts`, `modules/billing/service.ts` (demo checks), `modules/channels/service.ts` (demo checks), `integrations/carriers/index.ts`, `integrations/billing/index.ts`, `integrations/vendors/mailer.ts` (demo guard), vendor invite mail
- **grants likely needed** (see "every real-provider path" below): `integrations/channels/index.ts` (the adapter factory itself, not just `modules/channels/service.ts`), and either `modules/shipping/service.ts` + `modules/shipping/jobs.ts` (every `carrierAdapter()` call site) or a design that avoids touching them
- tests

## Acceptance criteria
1. **Which companies count as demo:** the exclusions key on "sample workspace" (`demoOwnerUserId IS NOT NULL`), not `companies.demo`.
   - `modules/tenancy/demo-flag.ts`'s `isDemoCompany()` is exactly this bug today — it reads `companies.demo`. Fix it there.
   - **But it has exactly one caller today** (`modules/channels/service.ts:369`, Shopify connect-time provider choice). Fixing the column alone does not give every real-provider path a guard — see AC2.
   - The seeded Desert Bloom gets the real behavior: plan limits and invite emails.
   - A regression test pins that.
   - The golden path still passes.
2. **Nothing real for a sample workspace — verified by grepping every adapter factory's call sites, not just the ones in this card's owned paths:**
   - **Carrier:** `carrierAdapter()`/`carrierTracking()` (`integrations/carriers/index.ts`) take **no company/context argument at all** today — they pick mock vs. live from a single global `env.mocks.carrier` flag. Every call site is in `modules/shipping/service.ts` (4 places) and `modules/shipping/jobs.ts` (1 place), none of them owned by this card. Making the guard per-company requires either (a) changing the factory's signature to take an `isDemo`/company argument and updating every one of those 5 call sites — needing a grant into shipping — or (b) some other mechanism; there is no ambient tenant context (`withTenant` only wraps a DB transaction, not a JS-level context) to hook into instead. Resolve which before starting.
   - **Marketplace/channels:** `getChannelAdapter()` (`integrations/channels/index.ts`) is called from **9 places across 4 files** — `modules/channels/service.ts` (owned, 3 call sites) and `modules/channels/sync.ts`, `modules/inventory/availability.ts`, and critically `modules/ai/service.ts:732` (the AI-listings publish path, B-101's own dead-branch line) — **none of the last three are in this card's owned paths.** Today's only guard is the connect-time provider choice for Shopify (AC1's fix); every other channel connects with no demo check at all, and every downstream caller just trusts the connection's stored `provider` column rather than re-checking demo status live. Recommend adding the live check once, inside `getChannelAdapter()` or `webhookAdapter()` itself (one small file, `integrations/channels/index.ts`), for defense in depth — cheaper than a grant into `ai/service.ts`, `availability.ts` and `sync.ts`, and it also closes the AI-publish gap for free.
   - **Blank suppliers are not in this AC at all, but should be:** `getSupplierAdapter()` (`integrations/suppliers/index.ts`) goes live whenever the company has its own S&S credentials (`modules/inventory/service.ts`), independent of demo status — a sample workspace with real S&S keys entered could place a real supplier order today. Raise this as a scope question (`scope-change-request`) rather than silently building it in; it's the same class of risk as the carrier/marketplace guards.
   - Stripe checkout and portal return a friendly `DEMO_MODE` error;
   - no emails are sent (invites, vendor, auth notices). `sendMail()` (`integrations/vendors/mailer.ts`, owned) is the one real choke point — `lib/auth-mail.ts` (auth notices) already funnels through it — **but `sendMail()` has no company/demo context today**, and its only caller with that context is `invites.ts`. Auth notices arrive from Better Auth's hooks in `auth.ts` (not owned) with just a `user`, not a company id, and a user could belong to more than one company — decide (and document) whether auth notices are gated by "any of the user's companies is real" or something narrower before wiring it up.
3. **Test with real keys:** set fake "real" keys (env flags) and show that a sample workspace never reaches the real adapters (spy or fetch-mock) — cover all of the call sites in AC2, not only the ones already inside this card's owned paths.
4. **Web:** shows the `DEMO_MODE` messages. Hand the strings to the web card or add them to the demo feature (T-5-3's path, granted).

## Verify
Run tsc, lint, test and build. Tests cover every guarded path. Curl on a DB copy: in a sample workspace, buy a label and check the mock was used; checkout returns `DEMO_MODE`.
