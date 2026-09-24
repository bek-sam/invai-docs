# Per-marketplace application checklists

Baseline checked 2026-09-24. Re-check every program page before using a row; programs change. `[U]` =
unverified, `[3P]` = third-party source only. "Our state" is a starting point from research 10 §9 and research
12 §7; verify it in code before writing `met`.

Copy one section into `invai-docs/compliance/packets/<marketplace>/packet.md` and add two columns:
`Status (met/gap/n/a)` and `Evidence or gap owner + backlog id + date`.

---

## 1. Etsy: Personal App, then Commercial Access

Sources: https://developers.etsy.com/documentation/ ,
https://developers.etsy.com/documentation/essentials/authentication , https://www.etsy.com/legal/api (403 to
fetchers; read via Wayback), https://www.etsy.com/legal/creativity , research 10 §3.

**Path:** create an app in the Developer Portal → Personal App review → request Commercial Access for that app
(separate manual review). Webhooks are set once per app in the portal.
**Timeline:** Personal App review then Commercial manual review, "weeks" each (research 10 §2); no official
duration is published [U]. Plan 4–8 weeks end to end, plus one resubmission.

| # | Requirement | Evidence to show | Our state (2026-09-24) |
|---|---|---|---|
| E1 | App name does not contain "Etsy" | Portal app name | Not created |
| E2 | Trademark notice, exact text: "The term 'Etsy' is a trademark of Etsy, Inc. This Application uses Etsy's API, but is not endorsed or certified by Etsy." shown prominently | Screenshot of web footer and the Etsy connect screen | Missing (M-26, B-14) |
| E3 | OAuth2 PKCE; `x-api-key: keystring:shared_secret`; refresh token rotated and stored atomically | `src/integrations/channels/etsy/` code + test | Adapter pending (M-2, B-05) |
| E4 | Minimum scopes only; each scope tied to a feature | Reviewer notes scope table | To write |
| E5 | Freshness: listing data ≤ 6 h stale, other data ≤ 24 h | Poll schedule + webhook design | To design |
| E6 | No analytics/ML/AI training on Etsy data; no ad-platform linking | DPA/ToS text, `decisions/0007-ai-model-policy.md`, zero-retention inference config | Check config |
| E7 | Never email or text Etsy buyers order, shipping or tracking info | Mailer code path excludes Etsy buyers; test | Missing guard (M-26, B-14) |
| E8 | Listings we help create follow Creativity Standards (AI disclosure about the design, `production_partner_ids`) | `listing-compliance-check` results; `src/ai/validators/listing.ts` | Wrong target (M-23, B-14) |
| E9 | Webhook verification (Standard Webhooks, multi-signature, 5-min tolerance), dedupe on `webhook-id` | `src/api/webhooks.ts` test | Wrong header (M-7, B-07) |
| E10 | Breach notice ≤ 24 h to `dpo@etsy.com` and the seller | Incident plan (`incident-response`) | No written plan (B-10) |
| E11 | Data kept no longer than reasonably necessary | Purge job `src/modules/orders/jobs.ts`; retention table | Met for PII (S-16); verify |
| E12 | Use the API, never scrape Etsy pages | Code review statement | Met (no scraping) — verify |

---

## 2. Amazon SP-API: public developer, restricted roles (PII)

Sources: https://developer-docs.amazon/sp-api/docs/register-as-a-public-developer ,
https://developer-docs.amazon/sp-api/docs/guidance-to-address-key-security-controls-in-sp-api-integration ,
https://developer-docs.amazon/sp-api/changelog/updates-to-the-data-protection-policy-and-acceptable-use-policy
, research 10 §4, research 12 §2.1.

**Path:** Solution Provider Portal → Developer Profile (org details, public website, roles, use case, security
control answers of under 500 characters each, policy agreement) → review. Restricted roles add Phase 1
(website and profile) and Phase 2 (data security assessment, architecture review of the PII flow). Public apps
must be listed in the Selling Partner Appstore.
**Timeline:** reply to any reviewer contact within **5 days** or the case closes. Review time is not published
[U]; plan 4–10 weeks after the profile is submitted. The critical path is our own prerequisites: every DPP row
closed, including an external pen test (vendor lead time 2–6 weeks [U]) and 30-day scanning running in CI.
**Scope note:** direct SP-API is out of the MVP (`decisions/0006-v1-cuts.md`) until the security review and
pen test are done.

| # | Requirement | Evidence to show | Our state |
|---|---|---|---|
| A1 | Every DPP control closed | `invai-docs/compliance/amazon-dpp/evidence-pack.md` (`amazon-dpp-evidence-pack`) | Many gaps |
| A2 | Public website with privacy policy and security contact | Live URL (owner) + `legal-doc-draft` output | Not live |
| A3 | Use case and role list; each role mapped to a feature | Reviewer notes | To write |
| A4 | PII data-flow diagram and protection controls | `data-flow.md` | To write |
| A5 | Restricted Data Tokens for v0 PII calls; v2026 Orders role-based | Adapter design note | Adapter pending |
| A6 | LWA client secret rotated every 180 days; re-auth every 365 days tracked | Credential calendar job | Missing (B-05) |
| A7 | Named Incident Management Point of Contact; 24 h notice to security@amazon.com | Incident plan with the owner's name | Missing (B-10) |
| A8 | Selling Partner Appstore listing | `app-store-listing`-style copy for Amazon | To write |

---

## 3. Shopify App Store (public app)

Sources: https://shopify.dev/docs/apps/launch/shopify-app-store/app-store-requirements ,
https://shopify.dev/docs/apps/launch/app-requirements-checklist ,
https://shopify.dev/docs/apps/launch/protected-customer-data ,
https://shopify.dev/docs/apps/build/compliance/privacy-law-compliance , research 10 §5.

**Path:** Partner Dashboard app → request protected customer data access (Level 2, per field: name, address,
email, phone) → complete the listing (`app-store-listing`) → submit with screencast and test credentials →
review.
**Timeline:** review time varies and is not guaranteed [U]; plan 2–4 weeks including one round of fixes.
Protected-data review happens in the same flow.

| # | Requirement | Evidence to show | Our state |
|---|---|---|---|
| S1 | Mandatory compliance webhooks `customers/data_request`, `customers/redact`, `shop/redact` in `shopify.app.toml`, HMAC-verified (401 on bad), acted on within 30 days | Handlers + tests; `privacy-request-handling` | Missing (M-3, G2, B-06) |
| S2 | Expiring offline tokens (`expiring=1`), refresh rotation (required for new public apps since 2026-04-01) | `exchangeShopifyCode` + refresh job | Missing (M-2, B-05) |
| S3 | Protected customer data Level 2 controls: encrypted backups, test/prod separation, access log for protected data, written incident policy, staff access limits | research 12 §2.2 rows with evidence | Partial (B-10, B-18) |
| S4 | Null PII without approval → "needs address" hold, never an empty label | Test on `shipTo: null` | Verify (M-6, B-28) |
| S5 | **Billing through Shopify App Pricing or the Billing API** (req. 1.2.1: off-platform billing cannot be distributed through the App Store) | Billing design | **Conflict:** InvAI bills with Stripe. Escalate before building |
| S6 | **Embedded experience in Shopify Admin with the latest App Bridge; session tokens; works without third-party cookies in Chrome incognito** (reqs. 2.2.2, 2.2.3, 1.1.1) | Embedded route demo | **Conflict:** `invai-web` is a standalone SPA. Escalate |
| S7 | GraphQL Admin API only; no API deprecated for 90+ days | Pinned API version in the adapter | Verify (2026-07 pinned) |
| S8 | Screencast of onboarding and features; valid test credentials with full access, including for third-party accounts | Screencast file; demo store | To make |
| S9 | Privacy policy URL; support contact; emergency developer contact | Live URLs (owner) | Not live |
| S10 | Webhook subscriptions app-scoped in TOML (shop-scoped ones get deleted after failures) | `shopify.app.toml` | Missing (M-3) |

---

## 4. TikTok Shop Partner Center (US)

Sources: https://partner.tiktokshop.com/docv2/page/app-review-process ,
https://partner.tiktokshop.com/docv2/page/data-security-and-privacy-review (JavaScript-only; content [U]),
research 10 §6, research 12 §2.3.

**Path:** Partner Center account → create app in the right category (a Connector app for us) → language
listing per market → App Requirement Document (ARD), design materials, testing details, screenshots →
design/ARD review → development and app review → compliance, legal, data security and privacy review → **beta
test (required for Connector apps targeting US or UK sellers)** → publish on the App and Service Store.
**Timeline:** custom apps reviewed at ≥ 25 shops in 5–7 business days [U]; the full Connector path with beta
is longer. Plan 6–10 weeks [U].

| # | Requirement | Evidence to show | Our state |
|---|---|---|---|
| T1 | ARD: scope, required APIs, data handling, testing evidence | ARD draft in the packet | To write |
| T2 | Data security and privacy review: assume Amazon-equivalent controls | Link the DPP evidence pack | Gaps as Amazon |
| T3 | Signed requests, per-endpoint API versions, `shop_cipher` | Adapter design | Adapter pending |
| T4 | Never send ON_HOLD orders to production; answer cancel requests within 24 h | Order-state design (B-12) | Missing (M-10) |
| T5 | Beta sellers for Connector review | Owner-recruited pilot shops | Owner |

---

## 5. Walmart Marketplace Solution Provider

Sources:
https://developer.walmart.com/us-marketplace/docs/app-registration-and-approval-process-for-publishing-to-app-store
, https://developer.walmart.com/us-marketplace/docs/oauth-20-authorization ,
https://developer.walmart.com/us-marketplace/docs/walmart-api-support-with-solution-provider-center , research
10 §7.

**Path:** sandbox testing → production app registration → technical and marketing details → Walmart review
with kickoff and **live demo calls** → App Store publication → marketing page.
**Timeline:** Walmart makes first contact 1–2 days after submission; approval takes **3–5 weeks** (research 10
§7). Plan 5–6 weeks with one resubmission.

| # | Requirement | Evidence to show | Our state |
|---|---|---|---|
| W1 | OAuth 2.0 authorization code (callback, login and client URLs), minimum scopes | Adapter config | Adapter pending (M-12) |
| W2 | Sandbox testing done | Test log in the packet | Not started |
| W3 | Marketing assets: square logo (SVG/PNG ≤ 1 MB), banners 1920×400 (≤ 5 MB), 200-character description, up to 5 feature bullets, pricing with activation steps, support URL | Asset files, copy from `app-store-listing` | To make |
| W4 | Live demo of the integration | Demo script from `build/demo-guide.md` | To write |
| W5 | PII out of URLs and logs, secrets in a vault, least privilege | research 12 §1.4, §1.10 evidence | Partial (B-18, B-23) |
| W6 | Acknowledge POs on intake; tracking after carrier handoff | Adapter design | Adapter pending |
