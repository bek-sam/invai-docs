# InvAI vendor inventory

Internal reference for the Amazon SP-API and Shopify App Store security questionnaires and for SOC 2
readiness (`research/12-security-quality-playbook.md` §2.6). Same vendor set as `legal/subprocessors.md`, with
who owns access, where the credential lives, and the rotation rule. Every "not yet" here is a real gap, not a
plan credited as done — see `invai-docs/security/v1-review.md` and the Amazon DPP evidence pack for the
tracked closure dates.

**MUST NOT** treat "planned" or "stubbed" as "in production" when answering a questionnaire
(`security-questionnaire` playbook).

| Vendor | Purpose | Data categories | Access owner | Key location | Rotation rule | Status |
|---|---|---|---|---|---|---|
| Amazon Web Services (AWS) | Hosting: Postgres, object storage, a provisioned KMS key | All service data | `[[OWNER: AWS account owner]]` | AWS IAM / SST-managed, not yet in `invai-infra/sst.config.ts` as a rotated secret | `[[OWNER: not written down yet — research 12 §2.1 flags this as missing]]` | Local dev live; production not deployed |
| Anthropic | AI listing drafts, trademark check, assistant | Scrubbed shop text only, never buyer PII | `[[OWNER: Anthropic account owner]]` | SST secret `AnthropicApiKey` (`invai-infra/sst.config.ts:77`); env var `ANTHROPIC_API_KEY` | `[[OWNER: no rotation cadence set]]` | Mock unless the key is set |
| EasyPost | Rates, labels, tracking | Ship-to address, parcel data | `[[OWNER: EasyPost account owner]]` | Env var `EASYPOST_API_KEY`, `EASYPOST_WEBHOOK_SECRET` (`invai-backend/src/env.ts:86,88`) — **not yet an SST-managed secret** | `[[OWNER]]` | Mock unless the key is set |
| Stripe | Subscription billing | Billing contact, subscription ids | `[[OWNER: Stripe account owner]]` | Env var `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` (`invai-backend/src/env.ts:93-94`) — **not yet an SST-managed secret** | `[[OWNER]]` | Stubbed, no live account |
| S&S Activewear | Blank-garment purchase orders | Ship-to address, item/quantity | **The Shop**, not InvAI — credentials are tenant-owned per Shop, no platform-wide credential (`invai-backend/src/env.ts:171-173` comment) | Stored per-tenant, encrypted like other channel credentials (same field-encryption mechanism as `buyer_pii`, `invai-backend/src/lib/crypto.ts`) | Shop's own responsibility; InvAI does not hold a master key for this vendor | Mock unless a Shop supplies its own account/API key |
| SanMar | Same, alternate supplier | Same | N/A | N/A | N/A | Deferred, not integrated (`invai-docs/decisions/0006-v1-cuts.md`) |
| Shopify (as an API/app credential, not a marketplace connection) | InvAI's own Shopify Partner app credentials, used to build the OAuth connection every Shop authorizes | None directly; enables per-Shop connections | `[[OWNER: Shopify Partner account owner]]` | SST secrets `ShopifyApiKey`, `ShopifyApiSecret` (`invai-infra/sst.config.ts:79-80`) | `[[OWNER: Shopify requires token/app-credential rotation practices — not written down]]` | Mock unless both are set |
| Email provider | Transactional and opt-in digest email | Recipient name/email | `[[OWNER: not chosen — see owner-inbox OI-13]]` | Env var `SMTP_URL`, `MAIL_FROM` (`invai-backend/src/env.ts:112-113`) | `[[OWNER]]` | Local dev uses Mailpit only; no production provider |
| Field encryption key (not a vendor, but the control that protects buyer PII at every vendor boundary) | Encrypts `buyer_pii` columns | N/A | `[[OWNER]]` | Env var `FIELD_ENCRYPTION_KEY` (`invai-backend/src/env.ts:74`); SST secret `FieldEncryptionKey` (`invai-infra/sst.config.ts:76`); an AWS KMS key is provisioned (`sst.config.ts:58` `fieldEncryptionKmsKey`) but **not yet used by the application** — the app manages its own key ring instead (`invai-backend/src/lib/crypto.ts`) | Key-ring rotation is supported in code (prepend a new key, old data still decrypts, per `invai-docs/build/runbook.md` §2) but no cadence is scheduled | Live |
| Better Auth session secret | Signs staff dashboard sessions | N/A | `[[OWNER]]` | SST secret `BetterAuthSecret` (`invai-infra/sst.config.ts:75`) | `[[OWNER: rotation signs everyone out — no cadence scheduled]]` | Live |

## Vendors with no data access found in code

Error tracking, product analytics, and any pen-test or vulnerability-scanning vendor: none exist in the
codebase today. `[[OWNER: name a vendor for each before the next Amazon DPP or Shopify questionnaire round,
or answer "No" honestly]]`

## How to use this for a questionnaire

Every "Access owner" and "Rotation rule" cell marked `[[OWNER: ...]]` is a real answer of "not yet" for a
security questionnaire, not "yes" — see `.claude/skills/security-questionnaire/SKILL.md` rule: "MUST NOT
answer 'Yes' without verified evidence."

---
*Last updated: 2026-09-28 (draft, verified against code and infra config on this date).*
