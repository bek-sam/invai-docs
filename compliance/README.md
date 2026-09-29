# invai-docs/compliance

What the compliance-officer owns and keeps current here. Nothing in this folder or in `invai-docs/legal/` is
submitted, published, signed or sent by an agent — everything outbound goes through the human owner
(`send-owner-draft`, `escalate-to-owner`).

## In this folder today

- `vendor-inventory.md` — every outside service InvAI's code can call, who owns access, where the credential
  lives, and the rotation rule. Feeds the Amazon SP-API and Shopify App Store security questionnaires.

## Related, not yet started

These are named in the compliance-officer's role file and playbooks but have no content yet as of this draft
(2026-09-28); each is created on first use by the playbook that owns it:
- `packets/<marketplace>/` — marketplace app application packets (Etsy, Amazon, Shopify, TikTok, Walmart),
  see `marketplace-app-application`.
- `amazon-dpp/evidence-pack.md` — the Amazon Data Protection Policy control-by-control evidence pack, see
  `amazon-dpp-evidence-pack`.
- `privacy-requests/log.md` — the PII-free log of data subject access/deletion requests, see
  `privacy-request-handling`.
- `questionnaires/` — saved security questionnaires and the reusable answer bank, see
  `security-questionnaire`.
- `policy-watch/` — dated, sourced policy-change findings, see `policy-change-watch`.
- `listing-checks/` — AI listing compliance spot-checks, see `listing-compliance-check`.

## Legal drafts

First drafts of InvAI's Terms of Service, Privacy Policy, Data Processing Agreement and public sub-processor
list live in `../legal/` (English) and `../legal/es/` (Spanish), built by `legal-doc-draft`. Every one of
those documents:
- starts "DRAFT for counsel review. Not in force." and stays that way until the owner records counsel's
  sign-off,
- uses `[[OWNER: ...]]` placeholders for anything a lawyer or the owner must decide (entity name, address,
  governing law, prices) — nothing is invented,
- cites the code behind every data-handling claim in an "Evidence" section, so a false "yes" cannot slip in.

As of 2026-09-28 these are drafted (T-21-1) and queued for the owner to decide on counsel engagement; see
`invai-docs/owner-inbox.md` for the entry number.

## Rules for anyone editing this folder or `../legal/`

- Every claim cites evidence: a file, a test, a config key, or a screenshot. "Not yet" is always an option;
  a false "yes" is not.
- Legal documents are marked "DRAFT for counsel review" until a lawyer has reviewed them and the owner has
  recorded sign-off. An agent never presents a draft as final.
- Nothing here is submitted, registered, signed or sent by an agent. The owner does it, through
  `send-owner-draft`.
- Control gaps go to their owning role (security, SRE, integrations) through the tech lead, with the deadline
  the marketplace or regulation sets.
