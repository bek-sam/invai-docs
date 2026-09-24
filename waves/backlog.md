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
| B-33 | `wrong_style` scan mismatch reason | architect + floor-engineer | v1-#15 | open |
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
