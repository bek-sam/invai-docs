---
name: privacy-retention-code-built
description: Tenant export/deletion and 18-month buyer-PII redaction already exist in code (wave 12 T-12-4); research 12 §2.7 and G13 are stale on this point.
metadata:
  type: project
---

Wave 12's T-12-4 built the full privacy module: `invai-backend/src/modules/privacy/service.ts` and
`jobs.ts`. It has tenant data export (`requestExport`/`runTenantExport`), soft-delete then 30-day hard purge
(`requestDeletion`, `cancelDeletion`, `hardPurgeCompany`, `HARD_PURGE_DELAY_MS = 30 * 86400_000`), and a daily
sweep that redacts buyer PII on any order older than 18 months regardless of marketplace
(`BUYER_PII_RETENTION_MONTHS = 18`, `redactStaleBuyerPii`).

**Why this matters:** `invai-docs/research/12-security-quality-playbook.md` §2.7 and its gap list (G13) still
say "18-month non-PII retention: missing" and "no tenant offboarding, export or DSAR tooling" — that was true
when research 12 was written but is now out of date. When citing retention/export facts for a legal draft or
questionnaire, read the code (`src/modules/privacy/service.ts`) rather than trusting that research doc's gap
table at face value; the code is the source of truth per `read-before-change`.

**How to apply:** next time a legal draft, DPP evidence pack, or security questionnaire needs a retention or
export/deletion claim, cite `src/modules/privacy/service.ts` directly and double check whether research 12's
gap rows still apply before repeating them as open gaps.

See also [[shopify-gdpr-webhooks-live]].
