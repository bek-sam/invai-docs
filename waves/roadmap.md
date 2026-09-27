# Roadmap to a complete MVP

Owner: `tech-lead`. Written 2026-09-24 after the full-codebase audit (`build/audit-2026-09-24.md`). The items are in `backlog.md` (B-01 to B-108). This file puts them in wave order.

## What "complete" means
The platform is complete when all of these are true:
1. **Every MVP scope item works end to end**, with UI, in English and Spanish (`product/scope.md` items 1–15). There are no dead buttons, no contract procedures without a use, and no scope item marked "partial".
2. **Adding a real key switches an integration from mock to live with no code change**: Anthropic, EasyPost, Shopify, Stripe, S&S and SES. In production, a missing key is an error, not a silent mock.
3. **It deploys to staging from CI** with one owner action: domains, HTTPS, migrations as a separate task, reference data, alarms and backups.
4. **All P0 and P1 security, idempotency and tenancy items are closed**, with tests.
5. **The golden path, role, offline and Spanish E2E suites pass in CI.**

Agents can't finish some things on their own. These are the owner's track (below): real keys, AWS accounts, domains, marketplace approvals, prices, legal review and the actual deploy. The code for all of them will be ready and in mock mode.

## Where we are (audit summary)
- Checks: typecheck, lint and unit tests pass in all 8 repos. The golden path is green when suites run in a clean sequence.
- **Blocking:** the backend `build` script is broken, so no Docker or AWS image can build. The AWS config has at least 4 deploy-time failures.
- **Done:** SKU mapper, gang sheets, vendor portal, personalization, trademark logic, AI assistant.
- **Partial:**
  - Order Hub
  - Shopify adapter
  - Floor: pack check, offline queue, receiving
  - Inventory
  - Shipping: live tracking, CSV-channel tracking export, voids
  - Profit: refunds, ad spend
  - AI listings export
  - Onboarding and demo
  - Invites: team and vendor invites are broken
- **Missing:** Stripe billing, password reset, production reference data, production guards against mocks.

## Owner decision (2026-09-25)
Waves 10 (deployable) and 11 (operable) are **deferred** until the owner is ready to go live. The order is now 6 → 7 → 8 → 9 → 12 → 13 → 14 → 15, with waves overlapping: the next wave's builders start while the current gate runs. Items from 10/11 that are purely local stay in their original waves only if they block local work. The rest waits (B-01, B-02, B-03, B-57, B-58, B-59, B-73, B-74, B-75, B-76, B-77, B-18 AWS parts, B-21 deploy parts).

## Wave plan
Each wave has at most 5 cards and 3–4 builders at once. Every card gets an independent review, and every wave ends with the integration gate (fresh seed plus the golden path) before anything is pushed. The order is P0 safety first, then scope completeness, then deploy, then hardening.

| Wave | Goal | Cards (backlog IDs) |
|---|---|---|
| **1** | Safe to put real keys in: nothing fakes success in production, and webhooks are trustworthy | B-56 backend build + B-50 prod mock guard · B-43 + B-07 + webhook part of B-63: verify-first webhooks and a persisted delivery table · B-55 S&S tenant keys + B-64 crash-safe POs · B-51 + B-52 team and vendor invites · B-54 reference data (trademarks, plans) |
| **2** | Money and accounts | B-53 Stripe billing (backend) · B-53 billing UI · B-09 + B-60 account security (backend) · B-09 + B-60 account security (web) · B-11 + B-44 + B-62 + B-67 crash-safe labels, tracking push, cancel voids |
| **3** | Integrations hardened | B-66 EasyPost live tracking (moved from wave 2) · B-04 + B-65 availability push that really runs · B-05 token refresh and expiry calendar · B-06 Shopify compliance webhooks · B-28 + rest of B-63 Shopify polling, paid filter, refunds, pagination · B-61 heavy work moved to jobs |
| **4** | Floor complete | B-94 pack completeness check · B-95 offline-queue hardening · B-96 receiving station · B-105 floor polish · B-33 `wrong_style` |
| **5** | Office web: orders and settings | B-84 order actions and shipment section · B-85 channels settings · B-90 shipping settings + B-67 voids · B-91 onboarding, Today + B-72 demo mode · B-92 team and stations |
| **6** | Office web: inventory, production, profit, AI | B-86 inventory UI · B-87 in-house print, reprints, bins and labels · B-88 ad spend and profit export · B-89 listing copy and export + B-101 · B-93 accessibility and i18n + B-42 |
| **7** | Multi-channel shops (CSV channels) and correct money | B-68 tracking export files · B-13 + B-70 fees and refunds · B-69 + B-40 label fee from the plan (after OI-1) · B-26 ship-by holidays · B-12 staleness and per-line cancel |
| **8** | AI and marketplace compliance | B-14 Etsy rules · B-15 prompt isolation and spend breaker · B-45 cost table and mock · B-46 trademark gate · B-48 eval harness |
| **9** | Imaging for real print shops | B-78 PDF/SVG input · B-79 sheet barcode and scannable QRs · B-80 long PDFs · B-81 personalization upgrades · B-19 imaging limits and auth |
| **10** | Deployable | B-57 SST fixes and domains · B-58 email in AWS · B-59 + B-01 migrate task and `invai_app` · B-02 + B-03 + B-74 Valkey, HTTPS, RDS · B-77 secrets + B-73 S3 |
| **11** | Operable | B-75 alarms and error tracking · B-76 deploy pipeline and CI · B-08 + B-21 scanning and CI hardening · B-18 observability · B-16 health and shutdown |
| **12** | Reliable at scale | B-17 retries and DLQ · B-20 rate limits and fairness · B-23 KMS, export and deletion · B-24 CSP · B-99 import races |
| **13** | Contracts and quality | B-82 floor version handshake · B-83 contract CI · B-104 contract drift · B-22 E2E in CI, property tests, axe · B-97 E2E coverage |
| **14** | Evidence and docs | B-71 side-effect tests · B-10 + B-29 policies and docs · B-98 help center · B-106 seed and runbook · B-47 path guard |
| **15** | P2 sweep | B-25, B-27, B-30, B-31, B-32, B-34, B-35, B-36 (out of scope unless approved), B-37, B-38, B-41, B-49, B-100, B-102, B-103, B-107 |
| **16** | Team harness (done 2026-09-27) | Fast check after each edit, verification gate, guard blocks recurring lessons, agent memory that loads |
| **17** | Assistant as business analyst (done 2026-09-27) | B-113: compare periods, ad performance, design insights, fulfillment health, prompt v4 |
| **(owner)** | Direct Etsy API | B-108, only if the owner approves OI-3; then it slots in after wave 3 |

## Owner's track (can't be done by agents)
| When | What | Unblocks |
|---|---|---|
| Now | Answer OI-1 (label fee and prices), OI-2 (Shopify App Store), OI-3 (direct Etsy API) | Waves 2, 7, B-108 |
| Before wave 10 ends | AWS account(s), GitHub OIDC deploy role, region, domain + Route53, deploy keys, GitHub `production` environment protection | First staging deploy |
| Wave 10 | `sst secret set` per stage, SES production access, first `sst deploy --stage staging` | Staging |
| Anytime | Real keys: Anthropic, EasyPost, Shopify app, Stripe, S&S | Mock → live |
| Anytime | Etsy developer app + commercial access application; Amazon, TikTok and Walmart approvals | Direct marketplace APIs |
| Before first paying shop | Lawyer review of terms, privacy, DPA (drafts from B-10 and B-98) | Launch |
