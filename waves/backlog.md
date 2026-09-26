# Backlog

Owned by the `tech-lead` and ranked by the `product-manager` (`prioritize-backlog`). Each item becomes a task card in a wave. IDs are stable; never reuse one.

Sources:
- `v1-#` is `build/v1-plan.md` §6.
- `M-#` is the code audit in `research/10-marketplace-engineering-rules.md`.
- `P-G#` is §10 of `research/11-platform-scale-playbook.md`.
- `S-G#` is the gaps in `research/12-security-quality-playbook.md`.
- `S-#` is `security/v1-review.md`.

Status is `open`, `planned (wave n)`, `done (wave n)` or `accepted`.

## P0: breaks in production, violates a policy, or blocks a pilot or approval
| ID | Item | Owner role | Source | Status |
|---|---|---|---|---|
| B-01 | RLS is bypassed in AWS because `DATABASE_URL` uses the RDS master user. Create `invai_app` in RDS (bootstrap) and connect as it | platform-sre + backend-foundation | P-G1, v1-#1 | open |
| B-02 | Valkey for BullMQ: cluster mode off, `noeviction` | platform-sre | P-G2 | open |
| B-03 | Deploy runs migrations as a separate step; HTTPS listener | platform-sre | P-G3, P-G4 | open |
| B-04 | Shopify `setAvailability` uses the removed `ignoreCompareQuantity`. Move to `changeFromQuantity` plus `@idempotent` | integrations-engineer | M-1 | open |
| B-05 | Token refresh and rotation for every channel, plus a credential-expiry calendar (Shopify expiring tokens, Amazon 180-day secret and 365-day re-auth, Walmart 1-year, TikTok) | integrations-engineer | M-2, M-28 | open |
| B-06 | Shopify compliance webhooks (`customers/data_request`, `customers/redact`, `shop/redact`), `shopify.app.toml`, and a subscription re-check | integrations-engineer + compliance-officer | M-3, S-G2 | open |
| B-07 | Etsy webhook dedupe uses a header that doesn't exist. Use `webhook-id`, a persisted delivery table (≥ 30 h), multi-signature verification, and fetch by ID | integrations-engineer | M-7, M-8 | open |
| B-08 | Dependency, secret and container scanning in CI (Amazon requires 30-day scans); Renovate or Dependabot | platform-sre + security-reviewer | S-G18 | open |
| B-09 | Email verification and MFA | backend-foundation | S-G1, S-15 | open |
| B-10 | Written incident-response plan, access-control policy, vendor inventory, DPA and sub-processor list | compliance-officer + platform-sre | S-G29 | open |
| B-43 | Generic webhook route enqueues before verifying the signature. Verify first (P0 security) | integrations-engineer | engineering-skills audit | open |

## P1: needed before the first paying shop or at the first real scale
| ID | Item | Owner role | Source | Status |
|---|---|---|---|---|
| B-11 | Label buy is not crash-safe (it can double-charge). Buy outside the transaction and read back before retrying; add EasyPost webhooks | integrations-engineer + backend-engineer (shipping) | M-13, M-14 | open |
| B-12 | Webhook staleness check (`updated_at`); per-line cancellation; hold on a buyer-cancel request; TikTok ON_HOLD | backend-engineer (orders) + architect | M-9, M-10 | open |
| B-13 | Tiered referral fees (Amazon, Walmart), refund fee recovery, Shopify sales tax, TikTok 8% (verify) | backend-engineer (finance) | M-18–22 | open |
| B-14 | Etsy AI disclosure aimed at designs, `production_partner_ids`, title rules, trademark notice; never email Etsy buyers | ai-engineer + compliance-officer | M-23–26 | open |
| B-15 | Untrusted text goes to Claude in delimited data blocks; global AI spend breaker | ai-engineer | S-G3, P-G18 | open |
| B-16 | DB timeouts, `/livez` vs `/health`, graceful SIGTERM | backend-foundation + platform-sre | P-G6–8 | open |
| B-17 | Retries with jitter, `UnrecoverableError`, DLQ alert and redrive; outbox purge and a parked-event alert | backend-foundation | P-G9–11 | open |
| B-18 | Observability baseline: OTel traces API → queue → imaging; logs with `company_id`, `request_id`, `trace_id`; redaction | platform-sre + backend-foundation | P-G14, S-G7 | open |
| B-19 | Imaging: concurrency limit, pixel cap, format allowlist, service auth | imaging-engineer | P-G15, S-G4 | open |
| B-20 | Per-tenant API rate limits and queue fairness; spread out the channel poll | backend-foundation | P-G12, P-G13 | open |
| B-21 | CI hardening: actions pinned by SHA, `permissions:`, images pinned by digest, non-root containers, deploy gated on tests | platform-sre | S-G15–17, S-G19 | open |
| B-22 | E2E in CI, property-based tests (money, sizes, nesting), axe accessibility checks | qa-engineer | S-G21–23 | open |
| B-23 | KMS field encryption instead of the static key; tenant export and deletion; 18-month retention | backend-foundation + security-reviewer | S-G11, S-G13 | open |
| B-24 | CSP and security headers in web and floor; SVG not served inline | web-engineer + floor-engineer | S-G5, S-G6 | open |
| B-25 | USPS SCAN form (end of day), address verification, rate TTL across price changes | integrations-engineer | M-15–17 | open |
| B-26 | Ship-by with postal holidays; Etsy CSV processing time | backend-engineer (orders) | M-11 | open |
| B-27 | QC and bin calls idempotent | backend-engineer (production) | v1-#8 | open |
| B-28 | Shopify polling misses orders; throttle by `throttleStatus`; null PII without Level 2 | integrations-engineer | M-4–6 | open |
| B-29 | Fix the docs: Amazon scan interval is 30 days (not 180), and the DPP 2025-11 items | security-reviewer | S-G31, M-27 | open |
| B-44 | `pushTracking` runs inside the DB transaction; a retry re-emails Etsy buyers. Move it out, idempotent per shipment | backend-engineer (shipping) | engineering-skills audit | open |
| B-45 | `tokensToCostCents` hard-codes Opus 5 prices; the AI mock throws on unknown prompts | ai-engineer | engineering-skills audit | open |
| B-46 | Trademark-risk gate in product: score ≥ 60 blocks publishing; 25–59 needs a recorded human review | ai-engineer + web-engineer | listing-compliance-check | open |

## P2 and later
| ID | Item | Owner role | Source | Status |
|---|---|---|---|---|
| B-30 | Composite tenant-scoped foreign keys | backend-foundation | S-26, S-G14 | open |
| B-31 | Floor SSE auth without a query-string token | backend-foundation + floor-engineer | v1-#4, S-30, S-G9 | open |
| B-32 | Blank shelf/bin locations in the pick list | backend-engineer (inventory) | v1-#7 | open |
| B-33 | `wrong_style` scan mismatch reason | architect + floor-engineer | v1-#15 | done (found already shipped in the wave 4 plan review; regression check in T-4-1) |
| B-34 | Seed: no negative stock; scale seed profiles (small, mid, large) | qa-engineer + backend-foundation | v1-#10 | open |
| B-35 | DTF defaults: 0.25 in gaps, 150 DPI floor, QC fail reasons, transfer-age warning, maintenance block | imaging-engineer + backend-engineer (production) | research 10 §DTF | open |
| B-36 | Bella+Canvas via SanMar | integrations-engineer | M-29 | open |
| B-37 | SSE connection fan-out; tenant-leading trigram indexes; autoscaling | platform-sre + backend-foundation | P-G16, P-G17, P-G20 | open |
| B-38 | Visual regression, runtime contract test, i18n drift check | qa-engineer | S-G24, S-G25, S-G27 | open |
| B-40 | Align `PLAN_CATALOG` label fees, `calc/cost_model.py` and the concept (after the owner answers OI-1) | product-manager + data-analyst + backend-engineer (billing) | unit-economics-model finding | open |
| B-41 | Film-use metric: report length-weighted use across all vendor sheets (69.8% on seed) as well as full sheets (86–91%) | data-analyst + imaging-engineer | define-metric finding | open |
| B-42 | Spanish relative times ("4 weeks ago") untranslated on Orders | web-engineer | ux finding | open |
| B-39 | Vendor accept/decline procedure | architect | v1-#16, S-27 | accepted for v1 |
| B-48 | Eval harness: `invai-backend/evals/` and `evals/run.ts`, one eval set per AI route | ai-engineer | decision 0007 | open |
| B-49 | Analytics scripts folder and first metric queries (`invai-backend/scripts/analytics/`) | data-analyst | define-metric | open |
| B-47 | Path-guard hook: block Write/Edit outside the card's owned paths (tech-lead and reviewer first) | platform-sre + security-reviewer | team review B4 | open |

## Added 2026-09-24 by the full-codebase audit (source: `waves/roadmap.md`)
Sources: `A-BE` backend audit, `A-FE` frontend audit, `A-INF` imaging/infra/contracts audit, `A-QA` baseline health run. Evidence with file:line is in `build/audit-2026-09-24.md`; the wave order is in `roadmap.md`.

### P0
| ID | Item | Owner role | Source | Status |
|---|---|---|---|---|
| B-50 | Production guard: refuse to boot or refuse side effects when carrier, billing, supplier or AI mocks are active with `NODE_ENV=production`; hide `mocks` from public `/health` | backend-foundation | A-BE, A-INF | open |
| B-51 | Team invites broken end to end (no invitation row, no email, member never activated, email can't sign up later); staff without email get PIN-only accounts | backend-foundation + web-engineer | A-BE, A-FE | open |
| B-52 | Vendor invite link points to `/vendor/accept?token=` which doesn't exist; `inviteToken` never read | backend-engineer (vendors) | A-BE | open |
| B-53 | Stripe billing: Checkout, webhook, customer portal, `changePlan` must not apply paid plans without payment, trial expiry job, `maxUsers`/`maxConnections` limits, credit packs, upgrade prompts, trial/past-due banners | backend-engineer (billing) + integrations-engineer + web-engineer | A-BE, A-FE | open |
| B-54 | Production reference data: trademark marks (and plans) loaded by a reference-seed step with no demo tenants | backend-foundation + ai-engineer | A-BE, A-INF | open |
| B-55 | Tenant POs fall back to InvAI's own S&S keys (`suppliers/index.ts`); never use platform keys for a tenant | integrations-engineer | A-BE | open |
| B-56 | `invai-backend` `pnpm build` fails (`tsup --noExternal`), so Docker/AWS images can't build; add build to the definition of done | backend-foundation | A-QA | open |
| B-57 | `sst.config.ts` deploy blockers: `imaging.url` on an internal service, worker env (`BETTER_AUTH_URL`, `WEB_ORIGIN`, `FLOOR_ORIGIN`), stage URLs, imaging S3 config (endpoint/keys/region), one registrable domain with ACM for app/floor/api | platform-sre + imaging-engineer | A-INF | open |
| B-58 | Email in AWS: `SMTP_URL`/`MAIL_FROM` in env schema, SES SMTP secret + IAM, DKIM/SPF/DMARC | platform-sre + backend-foundation | A-INF, A-BE | open |
| B-59 | Migrations in the prod image: compiled migrate entry + `drizzle/`, one-off ECS task: bootstrap `invai_app` (+ proxy secret) → migrate → reference seed (extends B-01, B-03) | platform-sre + backend-foundation | A-INF | open |

### P1
| ID | Item | Owner role | Source | Status |
|---|---|---|---|---|
| B-60 | Password reset, account page (name, password, sessions) | backend-foundation + web-engineer | A-BE, A-FE | open |
| B-61 | Heavy work off the request/transaction: CSV import, personalization renders (with retry job), `batchBuy`, carrier call under `FOR UPDATE` in `rateOrder` | backend-foundation + backend-engineer (orders, shipping, personalization) | A-BE | open |
| B-62 | Cancel/hold after a label: void the label and block the tracking push; check item state in `pushTracking*` | backend-engineer (orders + shipping) | A-BE | open |
| B-63 | Shopify: webhooks import unpaid orders; poll misses refunded/voided; line-item pagination; webhook-subscription failure surfaced; disconnect unsubscribes; persisted delivery table; OAuth state expiry (extends B-07, B-28) | integrations-engineer | A-BE | open |
| B-64 | `submitPo` crash-safe with idempotency key; `receivePo` idempotent; cancel at supplier | integrations-engineer + backend-engineer (inventory) | A-BE | open |
| B-65 | `listings`/`listing_variants` never written, so availability push is dead (extends B-04) | integrations-engineer + backend-engineer (inventory) | A-BE | open |
| B-66 | Live tracking: EasyPost tracker webhooks → `in_transit`/`delivered` (extends B-11) | integrations-engineer | A-BE | open |
| B-67 | Void labels for CSV channels (`NO_PUSH_CHANNELS`), void confirmation dialog | backend-engineer (shipping) + web-engineer | A-BE, A-FE | open |
| B-68 | Tracking export files for CSV channels (Etsy, Amazon shipping confirmation, TikTok, Walmart) + UI | integrations-engineer + web-engineer | A-BE, A-FE | open |
| B-69 | Label fee comes from the plan, not hard-coded `LABEL_FEE_CENTS = 4` (with B-40, OI-1) | backend-engineer (shipping) | A-BE | open |
| B-70 | Refunds after shipment ingested (Shopify + CSV) into profit (extends B-13) | backend-engineer (finance) + integrations-engineer | A-BE | open |
| B-71 | Tests for money/side-effect paths (`buyLabel`, `rateOrder`, `voidShipment`, `batchBuy`, `pushTracking`, `syncAvailability`, `publishDraft`, `renderItemArtwork`) and fetch-mocked live adapters (Shopify, EasyPost, S&S) | qa-engineer + owners | A-BE | open |
| B-72 | Web demo mode: start with sample data, reset, leave | backend-foundation + web-engineer | A-BE, A-FE | open |
| B-73 | S3 lifecycle rules match real keys; bucket CORS limited; versioning | platform-sre + architect | A-INF | open |
| B-74 | RDS production settings (size, backups, deletion protection, final snapshot, `force_ssl`, Pool `ssl`) (P-G5) | platform-sre + backend-foundation | A-INF | open |
| B-75 | Alarms, SNS, budget, 12-month log retention, error tracking (S-G30) | platform-sre | A-INF | open |
| B-76 | Deploy pipeline: pinned sibling SHAs gated on green CI, staging → prod promotion, smoke test, rollback, region; infra CI; Docker build in app CI; root `.dockerignore`; compose `full` profile | platform-sre | A-INF | open |
| B-77 | Missing SST secrets: FloorTokenSecret, SMTP_URL, MAIL_FROM, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, S&S; KMS grant. Since T-1-1, production boot refuses without them (or `ALLOW_MOCKS=true` for a demo stage) | platform-sre | A-INF | open |
| B-78 | Imaging input formats: PDF input (rasterize at target DPI) or reject at upload; SVG at target DPI | imaging-engineer | A-INF | open |
| B-79 | Sheet identity and scannability: transfer QRs rendered ≥ 300 DPI; sheet header barcode; sheet id in file name; configurable label gap with cut guide | imaging-engineer | A-INF | open |
| B-80 | PDFs over 200 in rely on `/UserUnit`: cap or verify on vendor RIPs | imaging-engineer + architect | A-INF | open |
| B-81 | Personalization: multi-line, stroke/outline, photo slot, font enum in contract, missing-glyph flag | imaging-engineer + architect | A-INF | open |
| B-82 | Floor API version handshake (reload signal, compat window for offline replay) | architect + floor-engineer | A-INF | open |
| B-83 | Contracts CI triggers consumer typechecks; versioning/changelog | architect + platform-sre | A-INF | open |
| B-84 | Orders UI: rush/flag/artwork/tags, shipment section, address edit for `address_check` holds (new procedure), correct tab counts, more views/filters, bulk cancel, export | web-engineer + architect | A-FE | open |
| B-85 | Channels settings: Shopify OAuth return message, import history, reconnect for pending/error | web-engineer | A-FE | open |
| B-86 | Inventory UI: manual PO create/edit, "mark placed manually" for suppliers with no API (production refuses `submitPo` for them since T-1-3), stock count, inventory & supplier settings (S&S account, lead/safety days, `reserveOnImport`) | web-engineer | A-FE | open |
| B-87 | Production UI: in-house print path (contract state), reprint queue + reasons report, bins with `BIN:` and `B:` labels | web-engineer + architect + product-designer | A-FE | open |
| B-88 | Profit UI: ad spend screen + CSV import, export, drill-down | web-engineer | A-FE | open |
| B-89 | AI listings UI: copy helpers + marketplace listing CSV with real SKUs/variants, publish status, credit ledger | web-engineer + ai-engineer | A-FE, A-BE | open |
| B-90 | Shipping settings: carriers, label format, weights per style | web-engineer | A-FE | open |
| B-91 | Onboarding checklist complete (address, carrier, tablet, designs, costs, plan), dismissable; Today stat links and alert translation | product-designer + web-engineer + backend-engineer (today) | A-FE | open |
| B-92 | Team & stations: resend/revoke invites, confirmations for role/owner/deactivate, edit station, revoke token | web-engineer | A-FE | open |
| B-93 | Accessibility & i18n: keyboard table rows, skip link, English strings in invai-ui/web errors/sign-up, `RelativeTime`/`Money` locale (extends B-42) | web-engineer + product-designer | A-FE | open |
| B-94 | Floor pack completeness check (decision 0002), new contract procedure | architect + floor-engineer + backend-engineer (production) | A-FE | open |
| B-95 | Floor offline queue: attempt limit and parking, view/clear rejected, alerts on rejected replay, correct attribution, warn on forget, `storage.persist()` | floor-engineer | A-FE | open |
| B-96 | Floor receiving station (POs, vendor transfers, counts) | floor-engineer + product-designer | A-FE | open |
| B-97 | E2E: floor offline replay, role permissions, Spanish, uncovered web/floor flows; fix flaky vendor step (`clickIfShown`) and sign-in rate limit in dev E2E | qa-engineer | A-FE, A-QA | open |
| B-98 | Help center (en/es), terms/privacy links at sign-up, in-app help link | docs-writer + compliance-officer | A-FE | open |

### P2
| ID | Item | Owner role | Source | Status |
|---|---|---|---|---|
| B-99 | Orders: `ON CONFLICT` import / per-connection lock; channel line edits; poller skips pending-approval connections | backend-engineer (orders) + integrations-engineer | A-BE | open |
| B-100 | Production jobs: scrap job id collision; retries on build/regenerate sheets; deterministic compose keys | backend-engineer (production) | A-BE, A-INF | open |
| B-101 | AI: dead publish branch, assistant stream finish on disconnect, empty assistant messages, `sku_suggestion` and `personalization_check` prompts | ai-engineer | A-BE | open |
| B-102 | Vendor sheet email: resend, send after commit | backend-engineer (vendors) | A-BE | open |
| B-103 | Imaging polish: template geometry, aspect/upscale flags, ICC profiles, mirror, input bounds (and contract bounds), gate mock endpoints, return render time, graceful shutdown + HEALTHCHECK, test gaps | imaging-engineer + architect | A-INF | open |
| B-104 | Contract drift: `stock.changed` never published, `listing.synced` never emitted; imaging API contract test; remove or build unused procedures | architect | A-INF, A-FE | open |
| B-105 | Floor polish: all 12 reprint reasons, truthful QC outcome, English leaks in Spanish, pack progress persisted, camera scanner, PWA icons and `lang` | floor-engineer | A-FE | open |
| B-106 | Seed collides with a running worker (`stock_levels` unique); runbook fixes (seed time, imaging first, worker stopped, E2E steps, `pnpm stop`, `ALLOW_MOCKS`, `SMTP_URL`, `MAIL_FROM`, `STRIPE_WEBHOOK_SECRET` from T-1-1) | backend-foundation + docs-writer | A-QA | open |
| B-107 | Security/cost details: WAF, S3 gateway endpoint, ARM Fargate, imaging scaling; bundle size over 500 kB | platform-sre + web-engineer + floor-engineer | A-INF, A-QA | open |
| B-108 | Direct Etsy Open API v3 adapter (OAuth PKCE, receipts sync, tracking push, ledger fees) in mock mode until approval — **needs owner scope approval (OI-3)** | integrations-engineer | owner request | open |
| B-109 | **P0 before real keys:** demo exclusions key on `demoOwnerUserId IS NOT NULL` (per-user sample workspaces), not `companies.demo`, since the seeded Desert Bloom currently skips plan limits and invite emails. Block label buys, Stripe checkout and vendor mail for sample workspaces. Add a regression test for Desert Bloom's real billing and email. | backend-foundation + integrations-engineer | T-5-3 review | open (wave 6) |
| B-110 | `Org.demoOwned` contract field, so the web stops detecting the user's sample shop by its slug | architect + web-engineer | T-5-3 review | open |
| B-111 | Seed gang-sheet film efficiency dropped to about 69% (61–80%) after the T-5-3 seed-builder refactor; it was 86–91%. Restore a realistic art-size mix so demo numbers are credible (lesson: "seed data shapes the product's numbers") | backend-foundation + imaging-engineer | T-9-2 A/B finding | open |
| B-112 | Wire the UI for 12 contract procedures that exist but have no screen yet (listed in `waves/13/reviews/plan-architect-r1.md`) | web-engineer | T-13-3 plan review | open |
