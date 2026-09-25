# Report: T-5-3 Onboarding checklist, Today fixes, demo mode
Author: backend-foundation + web-engineer on Opus 5.5

Card: T-5-3. Owners: backend-foundation (backend) and web-engineer (web). Scope: `product/scope.md#mvp-in` item 14 (B-91, B-72).
Risk flags: ui, tenancy. Co-reviewers: product-designer and security-reviewer.

## Commits (on `main`, not pushed)
| Repo | SHA | What |
|---|---|---|
| invai-backend | `1539d39` | Typecheck fix for the architect's wave 5 stubs (`pinOnly: false`, honest `false` checklist fields, pinOnly/no-email invite returns `NOT_IMPLEMENTED`) |
| invai-backend | `d22b6ac` | `companies.demoOwnerUserId` (nullable, unique, FK users cascade) + migration `0017_tenancy_demo_owner` |
| invai-backend | `72c1139` | Checklist, `today.dismissChecklist`, `tenancy.demo.*`, billing/mail/marketplace exclusions, seed builder, tests |
| invai-web | `3da9a73` | Checklist UI, demo banner/menu, Today links/hints/alerts, en+es strings |

## Built
- **Checklist** (`modules/tenancy/onboarding.ts`, extracted from `service.ts`). It has 11 steps, each computed from the shop's own data:
  - `shipFromAddress`: a location address or shipping settings' from address.
  - `carrier`: shipping settings exist with at least one allowed carrier.
  - `tabletPaired`: a station has `tokenIssuedAt`.
  - `designsUploaded`: at least one design.
  - `costsSet`: an audit `cost_settings.update` exists. The cost row alone isn't enough, because a profit run creates it with defaults.
  - `planChosen`: the subscription isn't trialing or trial_expired, or it's a demo company.
  - `dismissed` and `dismissedAt` live in `companies.settings.onboardingDismissedAt`.

  `today.dismissChecklist({dismissed})` hides the checklist or brings it back (shops only).
- **Demo** (`modules/tenancy/demo.ts`). There is one sample shop per user, found by `demoOwnerUserId`.
  - `start` finds or creates the sample shop, fills it through the seed builder under `withTenant` (48 orders, 36 historical + 12 due soon; no artwork or sheet renders), switches the session into it and returns `Me`.
  - `reset` retires the old sample shop and builds a fresh one.
  - `leave` switches to the first membership that isn't the user's own demo.
  - Vendor orgs and non-person sessions are refused. Concurrent calls in one process are deduplicated.
- **Exclusions**, keyed on `companies.demo`:
  - Billing: `org-hooks.ts` inserts no trial for a demo company. `expireTrials` skips demo companies. `assertWithinPlan` and `assertPaidActionAllowed` short-circuit through a new `hasPlan()` that replaces the old `companyType()`.
  - Marketplace: `channels/service.ts:367` forces `provider: "mock"`. That is the only `env.mocks` branch in the file; other connect paths already write `"mock"`, and adapters are chosen per row.
  - Mail: `inviteSenders()` now carries `demo`, and `sendInviteEmail` no-ops for it. That covers team invites and new-vendor invites.
- **Seed builder** (`db/seed/builder.ts`). This is the seed's shop-data code, parameterized by company, PRNG, transaction runner, history runner, profile, people, PINs, station token, vendor, volumes and renders.
  - `db:seed` passes the same PRNG and `FULL_VOLUME`.
  - Changes that are neutral for Desert Bloom: blanks are read through the runner; the timeline backdating runs after each batch of 20 orders instead of inline; the `stock_levels` insert became an upsert (the architect's worker-race note).
- **Web**:
  - `features/onboarding` (checklist, dismiss with undo toast, "Show setup checklist" in the account menu).
  - `features/demo` ("Try with sample data" in an empty workspace's checklist and in the account menu; Demo banner with Reset (confirm dialog) and Leave).
  - Today: cards link to `view=due_today|overdue|blocked`, hints are visible (two lines), and alert headlines are translated from `alert.kind`.
  - 41 new keys, added by hand to `en.ts`, `es.ts` and `scripts/i18n-es.json`; the diff is additions only.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Checklist: 11 steps from real data, links, dismiss per company, reopen from the menu | Yes | `onboarding.test.ts` (5 tests: every step ticks from its data, per company, dismiss/restore keeps other settings); `steps.test.ts`; screenshots 1, 5 |
| 2 Today: stat links, visible hints, alerts translated from kind | Yes, with one dependency | Links go to the `due_today`/`overdue`/`blocked` views, which T-5-1 is adding (tech lead confirmed). Until then they fall back to All. Screenshots 2, 3 |
| 3 Demo: start from an empty workspace and the menu; banner + Leave; Reset rebuilds; excluded from billing, mail and marketplace; RLS proven | Yes | `demo.test.ts` (11 tests: start, isolation incl. a cross-tenant id read, reuse, billing, org hook, Shopify mock with `env.mocks.shopify=false`, mail no-op, leave, reset, one per user, refusals); browser flow below |
| 4 `db:seed` still produces the same Desert Bloom data | Yes | Fingerprints in `reports/T-5-3/seed-fingerprint-*.txt`, method below |

## Checks I ran
| Repo | Command | Result |
|---|---|---|
| backend | `tsc --noEmit` / `biome check .` | clean / `Checked 249 files … No fixes applied` |
| backend | `vitest run` (`invai_test_t53`, Redis db 3) | `Test Files 65 passed (65)`, `Tests 463 passed (463)` |
| web | `tsc --noEmit` / `biome check .` / `vitest run` / `vite build` | clean / `Checked 135 files` / `13 files, 75 tests passed` / `built in 1.18s` |

Per the owner's token budget, I didn't run the golden-path E2E suites.

## Exercised for real
Setup: a copy of the dev DB (`invai_t53_copy`, migrated to 0017), the API on :3130 from a worktree at `72c1139` with mocks on and imaging off, and the web on :5133. A Playwright script drove the flow:
- A new shop signed up. `me.onboarding` had all 11 steps false. Screenshot 1 shows the checklist and the "Try with sample data" callout.
- **Start**: 1.8 s (the API fill is 1.5–2.2 s). The result is "Sample shop" with `demo: true` and two orgs. Screenshot 2 (en) and screenshot 3 (es) show the banner, 8 of 11 steps done and translated alerts.
- The Due today card opens `/orders?view=due_today`, and the demo's orders are listed.
- **Reset** (es confirm, screenshot 4): 1.8 s, and the result is a new company id.
- **Leave**: back in the real shop (same id, `demo: false`). `orders.list` returns 0 rows, and `GET /orders/<demo order id>` returns **404 NOT_FOUND**, so demo data isn't visible from the real company.
- Dismiss set `dismissedAt`. "Mostrar lista de configuración" in the account menu (screenshot 5) brought the checklist back.
- At 390 px (screenshot 6), horizontal overflow is 0 px.
- No console errors or 5xx responses, apart from that deliberate 404.

**Seed equality.** I seeded three empty DBs from a worktree with imaging off: the original code twice (A, C) and the refactored code once (B, run about 1 minute before C). I then compared fingerprints of all counts and the random-driven columns (ids and timestamps excluded; SQL in `seed-fingerprint.sql`).
- **B = C** on every line: 24 table counts, and hashes of orders, items, transition pairs, timeline offsets, sheets, shipments, stock, movements, ad spend, usage, connections, vendor and location.
- The one exception is which 6 at-risk orders get alerts. The seed's `limit 6` has no ORDER BY; the kind counts are equal (6 at risk, 9 low stock).
- A (run about 10 minutes earlier) differs from C in the same fields. The original seed mixes `now`/`startOfToday` into the order sort, so its output drifts with the clock. That is existing behaviour, not a regression.

## Decisions
- **Demo semantics are keyed on `companies.demo`,** as the card asks. The seeded Desert Bloom is also `demo=true`, so it too gets no plan limits, no invite emails and mock-only Shopify. Its subscription is active, so billing is unaffected. The banner, Reset and Leave appear only on the user's *own* sample shop.
- **Reset retires instead of deleting.** The `inventory_movements_append_only` trigger (migration 0001) refuses every DELETE, including the cascade from `companies`, even for the owner role. Rather than weaken that control, reset clears `demoOwnerUserId` and deletes the members, so nobody can open the old shop. The rows stay (`demo=true`, still excluded) and the S3 files under `{companyId}/` are deleted (best effort).
- **One narrow `withSystem` in a request path**, with a written reason in `demo.ts`. Backdating the sample timelines rewrites `order_item_transitions`, which is append-only for `invai_app`. The statements are pinned to the demo company id and the orders just built. Every other demo write runs under `withTenant`, and a test checks that no transition lands outside the demo company.
- **The demo fills inside the request**, not as a job. It takes about 2 s for 48 orders with no renders, and the contract returns `Me`, so the workspace has to exist when the call returns.
- **The web identifies the user's own demo by slug** `demo-<company id>` (`features/demo/is-own-demo.ts`), because `Org` has no field for it.
- **Two `costsSet` / `carrier` definitions:**
  - `carrier` follows the PM's wording, so opening Settings > Shipping ticks it, because the row is created with default carriers.
  - `costsSet` uses the audit signal, because the cost row is created automatically.
  - As a result, Desert Bloom now shows 10 of 11 steps ("Check your costs").

## Known gaps and follow-ups
- **Contract (architect):** add an explicit `Org.demoOwned` (or similar) so the web doesn't depend on the slug convention.
- **Alert text:** only the headline is translated. The detail line is the backend's English title (it carries the order number or SKU); in English the message is shown too. Adding `data` to `Alert` would allow full translation (architect/backend).
- **Retired demos accumulate** (about 50 orders per reset). A purge needs a sanctioned way past the inventory append-only trigger (security-reviewer decision), or can stay as is.
- **Demo Shopify connect in a live deployment** stops at "OAuth HMAC mismatch" (`channels/sync.ts:984`). It fails closed and never reaches a real store or claims a domain, but the demo user sees an error (integrations-engineer).
- **Other outbound paths not gated for demo** (not in my grant):
  - the known-vendor invite mail (`vendors/service.ts:232`, `deliverInviteMail` without `senders`) and vendor sheet emails;
  - carrier label buys use `env.mocks.carrier` globally, so a demo in a live deployment could buy a real label;
  - Stripe checkout (billing owner).
  Suggested fix: check `isDemoCompany()` (`modules/tenancy/demo-flag.ts`) at each of these.
- **Seed builder size warning (architect):** the refactor is about 1,500 moved lines. If review wants changes to it, split it into its own card next wave, as planned.
- **No imaging in my runs,** so the demo's designs used placeholder art. With imaging up, `start` renders about 40 sample designs, which will make it slower; measure before relying on it.
- **Double seeding across processes:** concurrent `start` calls are deduplicated only within one API process. The unique `demoOwnerUserId` prevents a second company.
- **Today's date line** ("Friday, September 25") uses the browser locale, not the app language. This was already the case before this card.

## Blocked by other owners
- `src/api/authz.test.ts:129` (security-reviewer) failed after the architect's `demo.*` stub used `org.read`. It passed in my later full run, so it seems to have been fixed upstream.
- Today's links depend on T-5-1 adding the `due_today`, `overdue` and `blocked` order views; the tech lead confirmed they are coming.

## Processes and data
- Stopped: API :3130 and web :5133 (PIDs 11263 and 11243); no leftovers.
- Dropped: `invai_t53_copy`, `invai_test_t53`, `invai_t53_seed{a,b,c}`. Redis db 3 flushed. Worktree `../invai-backend-t53` removed. Temp files removed.
- The shared dev DB was only used as the copy's template. `seed-output.json` in the main checkout was not written; the seeds ran in the worktree.
- Screenshots (6): `invai-docs/waves/5/reports/T-5-3/1-…6-*.png`, all looked at.
