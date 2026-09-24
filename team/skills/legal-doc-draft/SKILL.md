---
name: legal-doc-draft
description: Write first drafts of InvAI's legal documents - Terms of Service, privacy policy, Data Processing Agreement (GDPR Art. 28 + CCPA service-provider terms) and the public sub-processor list - built from verified facts about the product and always marked "DRAFT for counsel". Use for "ToS", "terms", "privacy policy", "DPA", "sub-processors", or when a marketplace application needs a policy URL.
---

# Legal doc draft

Counsel receives a draft that is accurate about what InvAI really does with data, lists its open questions,
and is never mistaken for a final document.

## When to use
- A marketplace application needs a privacy policy or terms URL (`marketplace-app-application`).
- Before the first paying shop with marketplace PII (backlog B-10: DPA and sub-processor list).
- A new sub-processor, data flow, AI feature or retention rule changes what the documents must say.
- Counsel returns comments (revise, then back to the owner).

## Where drafts live
`invai-docs/legal/<doc>/draft-vN.md` (created on first use): `terms/`, `privacy-policy/`, `dpa/`,
`subprocessors/`. Keep every version; never overwrite a version counsel has seen.

## Steps
1. **Collect the facts, don't assume them.** Read and cite:
   - data flow and retention: `research/12-security-quality-playbook.md` §2.4, §2.7;
     `invai-backend/src/modules/orders/jobs.ts` (`PII_RETENTION_DAYS`); `build/architecture-as-built.md`;
   - AI use: `decisions/0007-ai-model-policy.md`, `src/ai/pii.ts` (what is scrubbed before model calls);
   - marketplace terms that bind us: `research/10-marketplace-engineering-rules.md` §1 R14–R15, §3 (Etsy API
     Terms), §5 (Shopify);
   - security controls: the DPP pack (`amazon-dpp-evidence-pack`). Describe only controls that are `closed`;
     write planned ones as planned or leave them out.
   - billing: Stripe (mock today, `src/modules/billing/service.ts`), prices only as the owner approved.
2. **Start from the outline** in [outlines.md](outlines.md) for the document type.
3. **Put the banner first,** exactly:
   ```
   > DRAFT for counsel — not legal advice, not reviewed by a lawyer, not for publication. Version N, YYYY-MM-DD, compliance-officer.
   ```
4. **Write plain sentences** (`write-plain-language-copy`), in InvAI's words (shop, buyer, order item, label).
   Keep legal terms where they carry meaning (controller, processor, service provider, sub-processor).
5. **Mark every uncertain point** inline as `[COUNSEL: <question>]`: governing law, liability caps, indemnity,
   entity name and address, arbitration, age limits, international transfers mechanism (SCCs), breach-notice
   wording. Don't guess these; they are counsel's and the owner's calls.
6. **Sub-processor list:** one row per vendor with purpose, data categories, location, and a link to its DPA
   and security report. Verify each vendor is actually used in code or infra (`grep` the integration, check
   `invai-infra/sst.config.ts`); mark `planned` otherwise. Starting set from research 12 §2.4: AWS, Anthropic,
   EasyPost, Stripe, the email provider, error/analytics tools.
7. **Check consistency** across the four documents: the same retention periods, the same sub-processors, the
   same breach-notice target (24 h to shops), the same AI statement.
8. **Review:** a domain owner checks facts (security-reviewer for security sections, integrations-engineer for
   data flows). Then the owner decides on counsel with `escalate-to-owner` (engaging a lawyer costs money) and
   the draft goes to counsel through `send-owner-draft`.
9. **After counsel,** save counsel's version as a new file, list the changes, and update any page or packet
   that quotes it. Only the owner publishes.

## Rules (MUST / MUST NOT)
- MUST mark every draft "DRAFT for counsel" in the banner and in the file name's folder. Never present a draft
  as final or approved.
- MUST NOT publish, sign, send to counsel, or accept terms. The owner does.
- MUST NOT copy another company's legal text. Outlines and our facts only.
- MUST NOT state a control, certification (SOC 2, ISO 27001, PCI level) or retention that isn't verified. We
  qualify for PCI SAQ A only if Stripe Checkout (redirect) is used (research 12 §2.5).
- MUST include the terms marketplaces require of us: no sale or sharing of buyer data, no model training on
  marketplace data, Etsy trademark notice where Etsy is named, no emails to Etsy buyers about orders.
- MUST keep InvAI's role right: processor/service provider for buyer data, controller for account data.

## Done when
- `draft-vN.md` exists with the banner, every section of the outline, sources for each fact, and `[COUNSEL:
  …]` questions listed at the end.
- The four documents agree on retention, sub-processors, breach notice and AI use.
- Facts were reviewed by the domain owner, and an owner-inbox entry asks for counsel review.

## References
- [outlines.md](outlines.md): section outlines for ToS, privacy policy, DPA and sub-processor list
- GDPR Art. 28 https://gdpr-info.eu/art-28-gdpr/ , Art. 30 https://gdpr-info.eu/art-30-gdpr/ , Art. 33
  https://gdpr-info.eu/art-33-gdpr/ ; CCPA service provider 11 CCR §7051
  https://www.law.cornell.edu/regulations/california/11-CCR-7051
- `invai-docs/research/12-security-quality-playbook.md` §2.4–2.7
- Related playbooks: `privacy-request-handling`, `security-questionnaire`, `send-owner-draft`,
  `escalate-to-owner`
