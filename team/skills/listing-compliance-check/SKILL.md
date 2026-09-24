---
name: listing-compliance-check
description: Check InvAI listing drafts, or changes to listing validators and prompts, against marketplace policy - Etsy AI disclosure (about the design), production_partner_ids, Etsy title rules, the trademark-risk threshold, Amazon's synthetic-performer tag, TikTok claim bans. Use for "listing compliance", "AI disclosure", "Creativity Standards", "trademark risk".
---

# Listing compliance check

No AI listing draft reaches a marketplace with a missing disclosure, a false production claim, a banned title
character, an unreviewed high trademark risk or an exaggerated claim.

## When to use
- Reviewing a change to `invai-backend/src/ai/validators/listing.ts`, the listing prompts (`src/ai/prompts/`),
  `CHANNEL_RULES` in `invai-contracts/src/channels.ts`, or the trademark check
  (`src/modules/ai/trademark.ts`). You are co-reviewer with ai-engineer (operating-system "Who reviews whom").
- Writing acceptance criteria for backlog B-14 (Etsy disclosure, partner field, title rules, trademark notice)
  or B-35-style listing rules.
- Spot-checking listing drafts in the seeded demo (monthly) or a pilot shop's drafts when customer-success
  reports a takedown.
- After `policy-change-watch` finds a listing-rule change.

## Steps
1. **Load the rules** from [rules.md](rules.md) and re-check any rule dated more than 60 days ago against its
   source.
2. **Get the drafts.** Use the seeded demo (`owner@desertbloom.test`) in the running app, or the rows the
   ai-engineer names from `listing_drafts` in the local DB. Never pull a pilot's real listings into the repo;
   customer-success gives you scrubbed copies (`scrub-pii-fixture`).
3. **Run the checks** in [rules.md](rules.md) per channel on each draft: title, tags, description disclosure,
   production partner, images, claims, trademark result.
4. **Trademark threshold.** Run or read the trademark check (`ai.trademarkCheck`; `combineRisk` in
   `src/modules/ai/trademark.ts`: score ≥ 60 = `high`, ≥ 25 = `medium`, else `low`). The team rule:
   - `high`: never publish as is. The shop rewrites and re-checks, or records a reason it has rights (a
     license it holds).
   - `medium`: a human reviews the matches and ticks "reviewed" before publish; the reason is kept with the
     draft.
   - `low`: publish allowed after the normal human approval.
   The check is a risk score, not legal advice; the UI must say so (it does in `explain()`).
   If the product does not enforce this yet, that is a finding for ai-engineer and web-engineer.
5. **Write findings** in `invai-docs/compliance/listing-checks/YYYY-MM-DD-<scope>.md` (created on first use):
   ```
   | Draft / rule | Channel | Check | Result (pass/fail/warn) | Evidence (file:line or screenshot) | Rule source | Fix owner |
   ```
6. **Route fixes:** code and prompt fixes to ai-engineer (validators, prompts), imaging-engineer (image
   metadata), web-engineer (disclosure and approval UI), through the tech lead. Policy wording for shops (what
   to put in settings) to docs-writer for the help center.
7. **Block or pass.** As co-reviewer, block a change that removes a disclosure, loosens a validator, or
   publishes without human approval. Say which rule it breaks.

## Rules (MUST / MUST NOT)
- MUST treat Etsy's AI disclosure as being about the **item or design** made with AI, in the description.
  AI-written copy alone doesn't trigger it; saying so is optional (research 10 §3).
- MUST use the structured `production_partner_ids` field for Etsy when a partner produces the item. A sentence
  is not a substitute. A shop that prints in-house must not be described as using a partner (today's
  `PARTNER_DISCLOSURE` text is wrong for them: M-23).
- MUST keep a human approval on every AI publish (Amazon Agent Policy, TikTok AI edits, our own rule).
- MUST NOT approve claims that a product can't back: performance, "washes 100 times", "#1", fake scarcity, AI
  edits showing results the shirt doesn't have.
- MUST NOT use Etsy, Shopify or Amazon listing data to train or tune models (R15).
- MUST NOT give legal advice to shops. Rules and risk scores only; the shop decides.

## Done when
- Each draft or rule change in scope has a pass/fail/warn per check with evidence and the rule's source.
- Every fail has a fix owner and, for code, a backlog id or card.
- The review verdict (approve / block with rule) is written for the change under review.

## References
- [rules.md](rules.md): per-channel checks with sources
- `invai-docs/research/10-marketplace-engineering-rules.md` §3 (Etsy listings, API terms), §4 (Amazon listings
  and policy), §6 (TikTok content), §7 (Walmart listings), §9 items 23–26
- `invai-docs/research/12-security-quality-playbook.md` §1.9 (LLM output handling)
- `invai-docs/waves/backlog.md` B-14
- Related playbooks: `ai-feature-with-evals`, `policy-change-watch`, `independent-review`
