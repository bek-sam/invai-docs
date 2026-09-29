# Review of T-21-2 (round 1)

- Reviewer: security-reviewer on Sonnet 5
- Author: platform-sre on Sonnet 5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-docs show --stat b2d3565` | 3 files: `ops/README.md`, `ops/access-control.md`, `ops/incident-response.md` — matches owned paths exactly |
| `git -C invai-docs show --stat fa7e6cd` | 1 file: `waves/21/reports/T-21-2.md` — report only |
| Direct reads of every cited code path (`roles.ts`, `channels.ts:50`, `tenancy.ts:119,177`, `sst.config.ts`, `local/init.sql`, `deploy.yml`, `env.ts`) | all citations verified line-accurate (see below) |

### Citation spot check
| Claim | Cited | Verified |
|---|---|---|
| `channels.disconnect` permission `channels.manage` | `contract/channels.ts:50` | Exact |
| `team.deactivate` permission `team.manage` | `contract/tenancy.ts:119` | Exact |
| `stations.revokeToken` permission `stations.manage` | `contract/tenancy.ts:177` | Exact |
| `invai_app` no BYPASSRLS, owns no tables | `local/init.sql` | Exact — role created with `LOGIN PASSWORD`, granted via `ALTER DEFAULT PRIVILEGES`, no `BYPASSRLS` anywhere in the file |
| RDS "only provisions the master user", `invai_app` bootstrap missing | `sst.config.ts` comment | Exact — lines 32-35 state this plainly |
| `removal: "retain"`, `protect: true` only in production | `sst.config.ts` | Exact — line 18-19 |
| OIDC role placeholder ARN | `deploy.yml` | Exact — `arn:aws:iam::123456789012:role/invai-deploy` at line 91, top-level `permissions: id-token: write` at line 15-16 |
| SST secret names (`BetterAuthSecret`, `FieldEncryptionKey`, `AnthropicApiKey`, `EasyPostApiKey`, `ShopifyApiKey`, `ShopifyApiSecret`) | `sst.config.ts` | Exact — all 6 match lines 75-80 |
| `FIELD_ENCRYPTION_KEY` rotation by prepending a key, format `k2:<base64>,k1:<base64>` | `runbook.md` §2 | Exact — matches `runbook.md:64` verbatim |
| `shipTo`/buyer email/phone returned only under `orders.manage` | (doc references this generally) | Confirmed independently: `src/modules/orders/service.ts:138` `canSeeAddress = ctx.permissions.has("orders.manage")` |
| `OWNER_ONLY` = `billing.manage`, `org.export`, `org.delete`; admin = `SHOP_ALL` minus those | `roles.ts` | Exact — matches `roles.ts:110,224` verbatim |
| office: broad access but not `billing.manage`/`org.export`/`org.delete`/`inventory.adjust`/`purchasing.receive`/`production.override` | `roles.ts` `OFFICE` array | Exact — none of those six appear in `OFFICE` |
| designer: no shipping/finance/inventory access | `roles.ts` `DESIGNER` array | Exact — no `shipping.*`, `finance.*`, `inventory.*` in the array |
| vendor: `vendor_portal.read/update`, `team.read/manage`, `files.read`, `alerts.read`, no shop-side permission | `roles.ts` `VENDOR` array | Exact |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 (incident-response plan) | Yes | Severities, roles, detection sources (mapped to real `ALERT_KINDS`), 5 containment classes each naming a real command/procedure, Amazon 24h/GDPR 72h/Shopify/Etsy clocks, evidence handling, 48h postmortem — all present with citations that check out |
| 2 (access-control policy) | **Partially** | AWS, GitHub, DB roles, secrets, access review/offboarding sections are accurate and well-cited. The app roles/permissions section (§4) has one factual mismatch against `invai-contracts/src/roles.ts` — see Blocking findings |
| 3 (claims cite a file; owner actions marked `[[OWNER]]`) | Yes, with the one exception above | `[[OWNER]]` used consistently for every real gap (no invented completion dates or fabricated AWS state) |

## Blocking findings
1. `invai-docs/ops/access-control.md:78` — "presser/packer/receiver: narrow, floor-scoped permission sets (`production.scan`, `production.qc`, and role-specific extras — `packer` adds `shipping.buy`, `receiver` adds `inventory.adjust`/`purchasing.receive`)" claims all three floor roles share a `production.scan` + `production.qc` baseline. That's false for `receiver`: `invai-contracts/src/roles.ts`'s `RECEIVER` array (lines 197-209) has `production.scan` and `production.receive` but **not** `production.qc`. Only `PRESSER` and `PACKER` (lines 175-195) include `production.qc`. Failure scenario: this document is explicitly built as evidence for the Amazon DPP and Shopify security questionnaires (`access-control.md:5-7`) and the card's own acceptance criterion is "role/permission tables match `invai-contracts/src/roles.ts`" — a reviewer or auditor who trusts this line would believe a receiver-role account can pass/fail QC, which it cannot. One-line fix, e.g.: "presser/packer/receiver: narrow, floor-scoped permission sets (`production.scan` plus role-specific extras — presser/packer also get `production.qc`; packer adds `shipping.buy`; receiver adds `production.receive`, `inventory.adjust`, `inventory.count`, `purchasing.receive`)."

## Checks
- [x] Only owned paths changed (`git show --stat b2d3565`: `ops/README.md`, `ops/access-control.md`, `ops/incident-response.md`)
- [x] Nothing outside scope
- [x] N/A — docs-only card, no tests to weaken
- [x] Containment steps for key leak, tenant leak, PII exposure, payment/label runaway and marketplace token compromise are each executable: they name a real command (`sst secret set`, `channels.disconnect`, `stations.revokeToken`) or plainly say "needs AWS"/`[[OWNER]]` rather than assuming access the team doesn't have
- [x] Amazon 24h clock, shop 24h clock, GDPR 72h clock stated correctly and consistently with `legal/dpa.md` §7 (T-21-1) — no contradiction between the two cards' clocks
- [ ] Role/permission table fully matches `invai-contracts/src/roles.ts` — see blocking finding 1

## Optional notes (not blocking)
- `access-control.md` §5 lists `EASYPOST_WEBHOOK_SECRET`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `INTERNAL_ADMIN_TOKEN` as "not yet SST-managed" — confirmed accurate against `env.ts` and `sst.config.ts`, and it's good that this matches the same gap `vendor-inventory.md` (T-21-1) independently found.
- The Etsy breach-notice gap (§5 in `incident-response.md`) is honestly flagged as unresearched rather than invented — correct call per the report's own reasoning.
- Good cross-check: this document's role/permission narrative section is exactly the kind of hand-maintained table the file's own line 61 warns about ("generated by hand, not derived... reviewers re-check this table"). This review is that re-check, and it did catch a drift — worth a follow-up habit of running a quick per-role diff against `ROLE_PERMISSIONS` before wording bullet-point summaries like this one.

## Fix and re-verify
- Owner: platform-sre. One-line text fix in `invai-docs/ops/access-control.md:78`.
- Round 2: I will re-read the corrected line against `invai-contracts/src/roles.ts`'s `PRESSER`/`PACKER`/`RECEIVER` arrays and re-approve if the mismatch is gone and nothing else changed outside the owned paths.
