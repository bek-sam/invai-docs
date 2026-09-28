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
| B-104 | Contract drift: `stock.changed` never published, `listing.synced` never emitted; imaging API contract test; remove or build unused procedures | architect | A-INF, A-FE | done (T-13-3: `stock.changed` was already fine, checked; `listing.synced` removed, unused; imaging contract test added; `production.scanBatch` removed via ADR 0013, the other 12 stay open as B-112) |
| B-105 | Floor polish: all 12 reprint reasons, truthful QC outcome, English leaks in Spanish, pack progress persisted, camera scanner, PWA icons and `lang` | floor-engineer | A-FE | open |
| B-106 | Seed collides with a running worker (`stock_levels` unique); runbook fixes (seed time, imaging first, worker stopped, E2E steps, `pnpm stop`, `ALLOW_MOCKS`, `SMTP_URL`, `MAIL_FROM`, `STRIPE_WEBHOOK_SECRET` from T-1-1) | backend-foundation + docs-writer | A-QA | open |
| B-107 | Security/cost details: WAF, S3 gateway endpoint, ARM Fargate, imaging scaling; bundle size over 500 kB | platform-sre + web-engineer + floor-engineer | A-INF, A-QA | open |
| B-108 | Direct Etsy Open API v3 adapter (OAuth PKCE, receipts sync, tracking push, ledger fees) in mock mode until approval — **needs owner scope approval (OI-3)** | integrations-engineer | owner request | open |
| B-109 | **P0 before real keys:** demo exclusions key on `demoOwnerUserId IS NOT NULL` (per-user sample workspaces), not `companies.demo`, since the seeded Desert Bloom currently skips plan limits and invite emails. Block label buys, Stripe checkout and vendor mail for sample workspaces. Add a regression test for Desert Bloom's real billing and email. | backend-foundation + integrations-engineer | T-5-3 review | open (wave 6) |
| B-110 | `Org.demoOwned` contract field, so the web stops detecting the user's sample shop by its slug | architect + web-engineer | T-5-3 review | done (T-13-3) |
| B-111 | Seed gang-sheet film efficiency dropped to about 69% (61–80%) after the T-5-3 seed-builder refactor; it was 86–91%. Restore a realistic art-size mix so demo numbers are credible (lesson: "seed data shapes the product's numbers") | backend-foundation + imaging-engineer | T-9-2 A/B finding | open |
| B-112 | Wire the UI for 12 contract procedures that exist but have no screen yet (listed in `waves/13/reviews/plan-architect-r1.md`) | web-engineer | T-13-3 plan review | open |
| B-113 | Assistant as business analyst: 4 new read-only tools (`compare_periods`, `get_ad_performance`, `get_design_insights`, `get_fulfillment_health`), prompt v4 (tool memory, shop context, language, analyst mode), tool chips and starter questions | architect + ai-engineer + web-engineer | `specs/assistant-business-analyst.md`, scope.md#mvp-in item 13 | done (wave 17, pushed 2026-09-27) |
| B-114 | Mock assistant: a follow-up like "And only Etsy?" after an ads question re-routes to profit/orders tools instead of re-scoping `get_ad_performance` (a channel name counts as a keyword). Demo-only; the real model is unaffected. Found by the wave 17 gate | ai-engineer | `waves/17/reviews/gate.md` | open (P2) |
| B-115 | Hook gaps accepted in wave 16: edits made through Bash (`sed -i`) aren't tracked by the verification gate; the guard can't see commands built at runtime (script files, base64 + eval, `$(...)`); credit/spend breakers are checked once per assistant question, not per tool round | platform-sre + ai-engineer | `waves/16/reports/T-16-1.md`, `T-16-2.md`; `waves/17/reviews/T-17-3-security-reviewer-r1.md` | open (P2) |
| B-116 | Guard false positive: the push rule also matches the whole joined command, so a push followed by `tr -d` elsewhere on the line is denied as a ref deletion. Match push flags only within the push segment; add adversarial tests both ways | platform-sre | `team/lessons.md` 2026-09-27 | open (P2) |
| B-117 | Market signals, contract + ADR for the global market cache table: 4 assistant tool names, niche get/set, recommendation list and vote, signal/source/licence enums | architect | `specs/market-signals.md`, scope.md#market-signals (SCR-001, OI-6) | done (wave 18) |
| B-118 | Market providers behind one interface with deterministic mocks (Google Trends, Pinterest, Amazon pricing/catalog, Walmart pricing, Jungle Scout), Census real client + fixture, selection by key/connection, rate limits, outage switch | integrations-engineer | `specs/market-signals.md`, research 14 §4.2 | done (wave 18) |
| B-119 | Market module: niche taxonomy + mapper, signal engine (trend, yoy, seasonality, act-by, price position, density, margin at price), confidence, rules R1–R5, recommendation record, adoption/outcome jobs, nightly jobs, read service for the digest | backend-engineer (market) | `specs/market-signals.md`, research 14 §3 | done (wave 18) |
| B-120 | Assistant market tools (`get_market_trend`, `get_seasonality`, `get_price_position`, `simulate_price`), niche route, prompt v5 (market-facts rule, citations, sample-data label, refusal), validator, market evals | ai-engineer | `specs/market-signals.md` | done (wave 18) |
| B-121 | Web for market signals: tool chips, 3 starters, sample-data badge, recommendation votes, niche chip + change on the design page (en/es) | web-engineer + product-designer | `specs/market-signals.md` | done (wave 18) |
| B-122 | Weekly digest contract: `digest.*` procedures, `digest.ready` event, settings/preference schemas, permission mapping | architect | `specs/weekly-digest.md`, scope.md#weekly-digest (SCR-002, OI-7) | done (wave 19) |
| B-123 | Extract analyst-tool queries into shared services; `digest_narrative` route in shadow mode with placeholder-only validator, breaker and eval set | ai-engineer | `specs/weekly-digest.md`, research 15 §4.5 | done (wave 19) |
| B-124 | Digest module: sweep/build jobs, snapshot, detectors D1–D8, ranking, skip/repeat rules, Market watch read, en/es templates, cost controls, profit parity test | backend-engineer (digest) | `specs/weekly-digest.md` | done (wave 19) |
| B-125 | Digest email delivery: per-person notification preferences, deliver job, RFC 8058 one-click unsubscribe, signed click/unsubscribe routes, footer, skip and suppression rules | backend-foundation + integrations-engineer (mailer) | `specs/weekly-digest.md`, research 15 §4.7 | done (wave 19) |
| B-126 | Digest web: `/digests` pages, Today Monday card, opt-in prompt, Settings → Notifications, account toggle, public unsubscribe page, thumbs (en/es) | web-engineer + product-designer | `specs/weekly-digest.md` | done (wave 19) |
| B-127 | Real market adapters (Google Trends, Amazon pricing/catalog, Walmart pricing, Pinterest, Jungle Scout): switch from mock only after the approval or licence lands | integrations-engineer | scope.md "Later"; OI-9, OI-11, SP-API and Walmart approvals | open (blocked on owner/approvals) |
| B-128 | Before the first real digest email to a pilot: postal address in the footer, production sending subdomain with SPF/DKIM/DMARC, counsel's CAN-SPAM note; then flip email on | platform-sre + compliance-officer | OI-12, OI-13, OI-14 | open (blocked on owner) |
| B-129 | Digest AI summary from shadow to on: real-model eval of `digest_narrative` passes, the plan-credit question answered | ai-engineer + product-manager | OI-8; `specs/weekly-digest.md` open question 2 | open (blocked on OI-8) |
| B-130 | Demo seed: about 18 months of shipped order history (closed orders only, realistic seasonality incl. a Halloween and Q4 peak) so market trends and the digest's trailing weeks show real signals on the demo; must not change golden-path counts or Today's queues | backend-foundation + qa-engineer | wave 18 spec review (QA: seed has ~30 days of history) | open |
| B-131 | Market signals: detrend before computing the seasonality index (a rising niche currently reads partly as seasonality, which flattens the deseasonalized trend); spec Step 3 change + engine + tests | product-manager + backend-engineer (market) | wave 18 T-18-2 round 2 finding | open |
| B-132 | Assistant stream: Chrome logs `net::ERR_ABORTED` on every `ai.assistant.ask` although the response is 200 and complete (oRPC RPCLink cancels the reader after the last event); make the stream close cleanly, then remove QA's narrow allow-list in `watchPage` | architect + ai-engineer | wave 18 T-18-5 report | open |
| B-133 | Rate limits: cheap `ai.*` reads (`ai.credits.balance`, conversations) share the 20/min per-company `ai` bucket with `ai.assistant.ask` (`bucketFor()` in `src/api/orpc.ts`), so normal assistant use plus E2E trips `RATE_LIMITED`; give reads their own bucket | backend-foundation + security-reviewer | wave 18 T-18-5 QA co-review | done (wave 19, T-19-4) |
| B-134 | Shared `ConfidenceBadge` (and vote-card pattern) in `invai-ui`, replacing T-18-5's local component; needed again by the wave 19 digest | product-designer | wave 18 T-18-5 designer co-review | open |
| B-135 | Assistant answers show raw markdown (`**`, `_`) and the "Demo mode" footer stays English in Spanish answers; pick one side (render markdown in web or stop emitting it) and translate the footer | ai-engineer + web-engineer | wave 18 gate issues 2-3 | open |
| B-136 | Market R1 when the peak has already started: shows an act-by date in the past with "Act now" and "stock … before September" in late September; rule and wording for an in-progress peak (PM wording, engine fix) | backend-engineer (market) + product-manager | wave 18 gate issue 5, tech lead screen check | open |
| B-137 | Today alert body shows a raw ISO timestamp ("Ship-by was 2026-09-26T06:59:59.999Z"); format in shop time and language | backend-engineer (today) | wave 18 gate issue 4 | open |
| B-138 | QA `market.spec.ts` follow-ups: Spanish vote-button names, assert Spanish vote cards on the holidays starter, `firstAnswerWithVotes` reports 429 instead of blaming the seed | qa-engineer | wave 18 gate issue 7 | open |
| B-139 | Mailer logs the email subject verbatim; digest subjects carry the shop name and weekly net profit. Log a subject template key or hash instead | integrations-engineer | wave 19 T-19-4 integrations review | open |
| B-140 | Digest and market: an R1 seasonal-prep item whose act-by date has passed (peak already under way) still says "stock … before September" on Sep 28; filter or re-word past act-by items in `listDigestMarketItems` and the assistant (extends B-136, now also in the unattended digest) | backend-engineer (market, digest) + product-manager | wave 19 gate issue 1 | open |
| B-141 | Digest copy: Spanish heading shows an English date ("Semana del Mon, Sep 21"); percent-point changes shown as relative percents (margin "+26%", on-time "0%"); mock source date shows the end of the current week | web-engineer + backend-engineer (digest) + product-manager (rule) | wave 19 gate issues 2-4 | open |
| B-142 | Market AC28 second half: each market tool answers within 500 ms p95 with ≤ 20 rows on the large-shop profile (the scale test covers only the compute budget) | qa-engineer | wave 19 QA gate-tests review | open |

## Proposed (not approved): growth opportunities, 2026-09-28
Filed by the `product-manager` from `research/16-growth-opportunities.md` (source ids `G-##`). **Not approved and not scheduled.** Rows marked "in scope" can enter the next `prioritize-backlog` run once specced; rows with an SCR wait for the owner's answer to OI-17 (or a later SCR). The tech lead owns this table and may move or merge rows.

| ID | Item | Owner role | Source | Status |
|---|---|---|---|---|
| B-143 | Dispatch-scan guard: alert when a bought label has no carrier acceptance scan by the pickup cutoff or the channel's dispatch deadline; at-risk dispatch count per channel (after B-66, with B-25) | backend-engineer (shipping, today) + web-engineer | G-01; in scope items 1, 7 | proposed |
| B-144 | Design license record: source, license type, unit cap, subscription end, as-is allowed, channels, proof file; units-sold counter; warn at 80%, block sheet build at 100% (owner override); trademark check on uploaded/purchased designs | architect + backend-engineer (catalog, production) + web-engineer | G-03; SCR-003 (OI-17) | proposed (needs SCR) |
| B-145 | Carrier adjustments in profit: consume EasyPost `shipment.invoice.updated`, restate label cost and profit, weekly adjustments in the digest | integrations-engineer + backend-engineer (finance) | G-11; in scope items 7, 8 | proposed |
| B-146 | Q4 margin guard: fee tables with effective dates, nightly S&S blank price refresh, digest/Today detector for design margin drops (peak surcharge, fee, blank cost); suggest only | backend-engineer (finance, inventory, digest) + web-engineer | G-04; in scope items 6, 8, 17 | proposed |
| B-147 | Handling-time advisor: p90 import-to-ship per design × blank × channel from scans; recommended Amazon handling time and Etsy processing time; CSV export; never writes listings | backend-engineer (production, orders) + web-engineer | G-02; SCR-004 (OI-17) | proposed (needs SCR) |
| B-148 | Agent-ready listings: required structured attributes per channel (material, fit, care, color names, processing time) in drafts, validator completeness score, export | ai-engineer + web-engineer | G-10; in scope item 10 | proposed |
| B-149 | Remake and reship after shipment: linked remake units reuse the print file, REMAKE tag on sheets and floor, reship label, reason codes, cost to profit, claim status | architect + backend-engineer (orders, production, shipping, finance) + web-engineer + floor-engineer | G-05; SCR-005 (OI-17) | proposed (needs SCR) |
| B-150 | Capacity planner: 10-day load board, units due vs measured press and printer capacity minus maintenance block; suggestions only; no forecast model | backend-engineer (production, today) + web-engineer | G-06; SCR-006 (OI-17) | proposed (needs SCR) |
| B-151 | Design risk gate: OCR + trademark + USPTO TSDR + web image similarity (Vision or TinEye, mock first) + pHash vs own catalog; B-46 thresholds | integrations-engineer + ai-engineer + imaging-engineer + web-engineer | G-15; SCR-007 phase 1 (OI-17) | proposed (needs SCR, spend) |
| B-152 | Cash-flow view: 4-week expected payouts by channel (payout rules, reserves) vs committed spend (POs, labels, plan); reserve-risk flag. First check payout CSV fields with an import dry run | backend-engineer (finance) + web-engineer + customer-success (dry run) | G-09; SCR needed | proposed (needs SCR) |
| B-153 | Labor per piece and station throughput from scan gaps; measured labor cost into profit; per-person view off by default (compliance review) | backend-engineer (production, finance) + web-engineer | G-07; item 8 / SCR for per-person | proposed |
| B-154 | Switch-from importers: SKU maps (ShipStation/spreadsheet CSV), blank costs, bulk design upload, package presets, dry-run report | backend-engineer (catalog, inventory) + web-engineer | G-12; SCR needed | proposed (needs SCR) |
| B-155 | Several suppliers per blank SKU, preferred supplier, PO split per supplier; SanMar PromoStandards adapter in mock mode (extends B-36; reopens SanMar in decision 0006: SanMar exclusive on Bella+Canvas since 2026-06-29) | architect + integrations-engineer + backend-engineer (inventory) | G-08; SCR needed | proposed (needs SCR, SanMar account) |
| B-156 | Manual and wholesale orders with a signed proof-approval link (no invoicing or payments in phase 1) | architect + backend-engineer (orders) + web-engineer | G-16; SCR needed | proposed (needs SCR, OI-13) |
| B-157 | RIP handoff: sheet-id file naming per vendor template, today's sheets as a zip in print order (with B-79); desktop hot-folder agent later | imaging-engineer + web-engineer | G-17; item 4 / SCR for agent | proposed |
| B-158 | Pack photo proof: one photo per order at pack, no label or PII in frame, 90-day retention | floor-engineer + backend-engineer (production) | G-13; SCR needed | proposed (needs SCR) |
| B-159 | Original AI designs from a niche brief: image-gen adapter with mock, generation jobs, upscale and background removal, hoodie mockup, Ideas screen, batch approval, credits, evals; publish Shopify first | ai-engineer + integrations-engineer + imaging-engineer + web-engineer | G-14; SCR-007 phase 2 (OI-17), reopens decision 0006 | proposed (needs SCR, spend) |
| B-160 | Amazon Buy Shipping labels (on-time delivery protection) | integrations-engineer | G-19; Later | blocked (SP-API approval) |
| B-161 | TikTok creator sample tracker (sample cost and return per creator) | backend-engineer (finance) | G-18; Later | blocked (TikTok Partner approval) |

## Proposed: analytics v2 (data-analyst, 2026-09-28)
Filed by the `data-analyst` from `specs/business-analytics-v2.md` (owner direction 2026-09-28). **Not approved and not scheduled.** In-scope rows need the PM's confirmation; gated rows need the owner's answer to OI-18. Overlaps with the growth rows are reconciled in the spec (B-152 cash view = T-A14, B-153 = inside T-A4, B-146 shares D12).

| ID | Item | Owner role | Source | Status |
|---|---|---|---|---|
| B-168 | Analytics-ready seed: 18 months of closed history with a Q4 peak, some late shipments, realistic scan intervals, POs with price changes and lead times, a few repeat Shopify buyers, several reprint reasons; golden-path counts and Today queues unchanged (absorbs B-130) | backend-foundation + qa-engineer | `specs/business-analytics-v2.md` T-A1; metric tests on seed | proposed (in scope, PM to confirm) |
| B-169 | Analytics contract: `analytics.*` read procedures (unitEconomics, losingOrders, leakage, shippingMargin, profitBridge, breakEven, operations, inventoryHealth, supplierTrends, designLifecycle, export), `CostSettings.fixedMonthlyCents`, `Shipment.destZone`, v6 assistant tool names | architect | spec T-A2 | proposed (in scope, PM to confirm) |
| B-170 | Finance analytics service: CM1/CM2/CM3 ladder, losing orders, revenue leakage, shipping margin, profit bridge, break-even; `fixed_monthly_cents` migration; one shared function with Profit page, assistant and digest (parity test) | backend-engineer (finance) | spec T-A3; `metrics/definitions/{contribution_margin,losing_order_rate,revenue_leakage,shipping_margin,profit_bridge,break_even}.md` | proposed (in scope, PM to confirm) |
| B-171 | Operations and shipping analytics: reprint and film waste in $, waits per step and bottleneck, measured press time (implements B-153), late-shipment drivers; `shipments.dest_zone` stored at label time (zone number only, no address) | backend-engineer (production, shipping) | spec T-A4; B-153 | proposed (in scope, PM to confirm) |
| B-172 | Inventory and design analytics: blank turns, dead stock value, size-mix gap, stockout exposure, supplier price and lead-time trends, design lifecycle stage; size split on reorder suggestions (suggestion only) | backend-engineer (inventory) | spec T-A5 | proposed (in scope, PM to confirm) |
| B-173 | Web Profit v2: contribution view, losing orders, leakage waterfall, shipping profit tab, why-changed bridge, break-even card, fixed-cost setting, CSV on each view (en/es) | web-engineer + product-designer | spec T-A6 | proposed (in scope, PM to confirm) |
| B-174 | Web Operations and Inventory health screens; lifecycle column on Designs (en/es) | web-engineer + product-designer | spec T-A7 | proposed (in scope, PM to confirm) |
| B-175 | Assistant tools v6 (`get_unit_economics`, `explain_profit_change`, `get_operations_health`, `get_inventory_health`, `get_shipping_insights`), prompt v6 'why with evidence', evals | ai-engineer | spec T-A8 | proposed (in scope, PM to confirm) |
| B-176 | Digest detectors D9 shipping loss, D10 losing orders, D11 dead stock/size gap, D12 blank price up (with B-146), D13 break-even pace; D2 names the bridge's top mover | backend-engineer (digest) + product-manager (wording) | spec T-A9 | proposed (in scope, PM to confirm) |
| B-177 | Today actions panel: up to 5 ranked actions with $ impact from the digest detectors on a trailing 7 days, clicks recorded | backend-engineer (today) + web-engineer | spec T-A10 | proposed (in scope, PM to confirm) |
| B-178 | Goals and targets with pace (net profit, on-time, reprint rate, film use) | architect + backend-engineer + web-engineer | spec T-A11; `metrics/scope-change-draft-analytics-v2.md` | proposed (needs SCR, owner OI) |
| B-179 | Anomaly alerts: robust z on daily orders, net, fee rate, refund rate; needs 8 weeks of history per shop | backend-engineer (today) | spec T-A12 | proposed (needs SCR, owner OI) |
| B-180 | Customer analytics: keyed buyer id (hash of channel buyer id), repeat rate, cohorts, contribution per buyer, RFM; Shopify first, Amazon never, others after compliance review; counts only | backend-foundation + backend-engineer + web-engineer + compliance-officer | spec T-A13; `metrics/definitions/repeat_buyer_rate.md` (draft) | proposed (needs SCR, owner OI, compliance) |
| B-181 | Scheduled report emails (monthly P&L CSV to named people) | backend-foundation + web-engineer | spec T-A15 | proposed (blocked on OI-12, OI-13, OI-14) |
| B-182 | Move `invai-docs/metrics/sql/*.sql` to `invai-backend/scripts/analytics/` once T-20-5's `scripts/**` grant ends (part of B-49); approved aggregated read-only views for use outside local | data-analyst + backend-foundation (views) | B-49; `metrics/definitions/README.md` | proposed |
| B-183 | Amazon CSV: `orders.shipping_cents` is 0 for every Amazon order; check whether the export carries shipping credits and map them (shipping margin and revenue are understated otherwise) | integrations-engineer | `metrics/definitions/shipping_margin.md` caveat | open (verify) |
