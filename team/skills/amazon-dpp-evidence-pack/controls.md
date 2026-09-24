# Amazon DPP controls: starting table

Baseline from research 12 §2.1 and §7, research 10 §4 and §9, and `security/v1-review.md`, as of 2026-09-24. "Our evidence" is where to look; verify before marking anything closed.

Sources: [DPP/AUP update 2025-11](https://developer-docs.amazon/sp-api/changelog/updates-to-the-data-protection-policy-and-acceptable-use-policy), [key security controls](https://developer-docs.amazon/sp-api/docs/guidance-to-address-key-security-controls-in-sp-api-integration), [vulnerability management](https://developer-docs.amazon/sp-api/docs/vulnerability-management).

| ID | Requirement | Our evidence (where to verify) | Gap (2026-09-24) | Owner | Backlog | Status |
|---|---|---|---|---|---|---|
| D1 | MFA on every account that can reach PII (app owner/admin, AWS, GitHub) | `invai-backend/src/auth.ts` (look for `twoFactor`) | No 2FA plugin; no MFA policy for staff accounts | backend-foundation; owner (staff accounts) | B-09 | open |
| D2 | Passwords ≥ 12 chars, lockout after 10 failures, history of 10 | `src/auth.ts` password settings; per-IP limits S-19 | Min length unverified; no per-account lockout or history | backend-foundation | B-09 | partial |
| D3 | Encryption in transit TLS 1.2+ | ALB/CloudFront config in `invai-infra/sst.config.ts` | HTTPS listener not yet set (B-03) | platform-sre | B-03 | open |
| D4 | Encryption at rest (AES-256) for PII | `encryptedText` columns in `src/db/schema/orders.ts` (`buyer_pii`); `src/lib/crypto.ts` | RDS/S3/ElastiCache KMS at rest to confirm | platform-sre | B-23 | partial |
| D5 | Key management system; API key rotation | `FIELD_ENCRYPTION_KMS_KEY_ARN` in `sst.config.ts` | App still uses static `FIELD_ENCRYPTION_KEY` (G11) | backend-foundation + security-reviewer | B-23 | open |
| D6 | PII deleted ≤ 30 days after delivery | `purgeBuyerPii`, `purgePiiObjects` in `src/modules/orders/jobs.ts`; `purge.test.ts` | Delivery events not ingested yet (falls back to shipped + 30 d, stricter); purge run record and failure alert | integrations-engineer; platform-sre | B-11, B-18 | partial |
| D7 | Non-PII Amazon data kept ≤ 18 months | — | No sweep (research 12 §2.7) | backend-foundation | B-23 | open |
| D8 | PII in job payloads, outbox, Redis, AI logs ≤ 30 days | `src/lib/queues.ts` `removeOnComplete`; `src/lib/outbox.ts` | Unverified (research 12 §2.7 "check") | backend-foundation | B-17 | open |
| D9 | Security logs ≥ 12 months, centralized, tamper-evident; access log for PII | `audit_log` (`src/lib/audit.ts`), append-only | No CloudWatch retention/Object Lock archive (G30) | platform-sre | B-18 | partial |
| D10 | No PII or secrets in logs | `src/lib/log.ts` | No redaction layer; Drizzle params logged (S-29, G7) | backend-foundation | B-18 | open |
| D11 | Vulnerability scan every 30 days; code scan each release | CI workflows in each repo | No scanning (G18) | platform-sre + security-reviewer | B-08 | open |
| D12 | Pen test every 365 days, retest after fixes | Pen-test report (vendor) | None; owner hires the vendor | owner + security-reviewer | — (propose) | open |
| D13 | Fix critical ≤ 7 days, high ≤ 30 days | Written SLA + tracking | Not written (docs still say 180-day scans: B-29) | security-reviewer | B-29 | open |
| D14 | Named Incident Management Point of Contact; notify security@amazon.com ≤ 24 h | Incident-response plan in `invai-docs/ops/` | No written plan (G29) | platform-sre + compliance-officer; owner is IMPOC | B-10 | open |
| D15 | Quarterly access reviews; revoke within 24 h of offboarding | Access-control policy; review records | Not written | compliance-officer + platform-sre | B-10 | open |
| D16 | Least-privilege access to PII in the app | `ROLE_PERMISSIONS` in `invai-contracts`; `shipTo` only with `orders.manage`; `authz.test.ts` | `buyerName` visible to every `orders.read` role (S-29) | backend-engineer (orders) | — (propose) | partial |
| D17 | Tenant isolation of PII | RLS on every `company_id` table, `src/db/rls-coverage.test.ts`; S-04 fixed | RDS still uses master user in AWS (B-01) | platform-sre + backend-foundation | B-01 | partial |
| D18 | Geo-dispersed, encrypted backups | RDS snapshot settings in `sst.config.ts` | Cross-region copy unchecked | platform-sre | — (propose) | open |
| D19 | Sub-processor risk assessments (AWS, Anthropic, EasyPost, Stripe, email provider) | Vendor inventory in `invai-docs/compliance/` | Not written (G29) | compliance-officer | B-10 | open |
| D20 | Network protection: WAF, private subnets for DB/Redis | `sst.config.ts` | WAF not set | platform-sre | — (propose) | open |
| D21 | LWA client secret rotated every 180 days; re-auth at 365 days tracked | Credential calendar job | Missing | integrations-engineer | B-05 | open |
| D22 | Restricted Data Tokens for v0 PII calls; no PII fetched beyond need | Amazon adapter design | Adapter not built (deferred, decision 0006) | integrations-engineer | — | open |
| D23 | Amazon data not used for model training; zero-retention inference | `decisions/0007-ai-model-policy.md`; provider config | Verify the zero-retention setting with the owner | ai-engineer | — | partial |
| D24 | Email verification before account use (Amazon asks about account security) | Better Auth `emailVerification` | Missing (S-15) | backend-foundation | B-09 | open |

Add a "Clocks" section under the table:

| Clock | Rule | Last done | Next due |
|---|---|---|---|
| Vulnerability scan | every 30 days | | |
| Pen test | every 365 days | | |
| Access review | quarterly | | |
| LWA secret rotation | every 180 days | | |
| Security-log retention check | quarterly | | |
