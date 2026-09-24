---
name: marketplace-app-application
description: Build InvAI's approval packet for a marketplace app program - Etsy Commercial Access, Amazon SP-API public developer (restricted PII roles), Shopify App Store, TikTok Shop Partner, Walmart Solution Provider - with requirements, evidence, screenshots, data-flow diagram, reviewer notes and a realistic timeline. Use for "apply", "app review", "commercial access", "SP-API", "App Store submission".
---

# Marketplace app application

Each marketplace application has a packet where every requirement points to real evidence or to an owned gap
with a date, and the owner submits it.

## When to use
- Starting or refreshing an application for Etsy, Amazon, Shopify, TikTok Shop or Walmart.
- A marketplace reviewer asked questions or rejected a submission.
- `policy-change-watch` found a change to a program's requirements.
- Before the PM ranks an item that depends on an approval (approval time is part of `prioritize-backlog`).

## Where the packet lives
`invai-docs/compliance/packets/<marketplace>/` (created on first use), with:
- `packet.md`: status line, the checklist from [checklists.md](checklists.md) with evidence, gaps, timeline,
  reviewer notes
- `data-flow.md`: the data-flow diagram (Mermaid) and the data inventory
- `screenshots/`: PNGs from the running app with demo data only
- `reviewer-notes.md`: the text the reviewer reads (test account, steps, scopes and why)

## Steps
1. **Read the rules first:** `research/10-marketplace-engineering-rules.md` §1 and the marketplace's section
   (§3 Etsy, §4 Amazon, §5 Shopify, §6 TikTok, §7 Walmart), `research/12-security-quality-playbook.md` §2,
   `security/v1-review.md`, decision `0006-v1-cuts.md` (direct Amazon, Etsy, TikTok, Walmart APIs are deferred
   until approvals and reviews land).
2. **Re-check the program page live** (WebFetch the URLs in the checklist). Note the date checked. If a page
   can't be read (Etsy returns 403, TikTok Partner Center needs JavaScript), say so and mark those rows `[U]`.
3. **Copy the marketplace's checklist** from [checklists.md](checklists.md) into `packet.md`. For each row
   write one of:
   - `met`: evidence = a file and line, a test name, a config key or a screenshot path. Verify it yourself
     (`grep`, open the file, run the test). You never assert a control you have not seen.
   - `gap`: the owner role, the backlog id (for example `B-06`) and the date the marketplace needs it. A gap
     with no backlog item goes to the tech lead as a proposed row (see `policy-change-watch` step 6).
   - `n/a`: with the reason.
4. **Draw the data flow** in `data-flow.md`: marketplace → webhook/poll (`invai-backend/src/api/webhooks.ts`,
   `src/integrations/channels/<channel>/`) → `orders` and encrypted `buyer_pii` (`src/db/schema/orders.ts`) →
   S3 raw/label objects → EasyPost → label PDF and packing slip → purge (`src/modules/orders/jobs.ts`,
   `PII_RETENTION_DAYS = 30`). Add which fields leave to which sub-processor (Anthropic gets scrubbed text
   only, `src/ai/pii.ts`). Take the facts from `build/architecture-as-built.md` and the code, not from memory.
5. **Take screenshots** from the running app with the seed data (`CLAUDE.md` "Demo data";
   `owner@desertbloom.test`). Use `.claude/skills/ux-audit/shoot.mjs` for the standard viewports, or a one-off
   Playwright script for the exact size a marketplace wants. Check each image by eye: no real names, no
   secrets, no "mock" labels the reviewer would misread.
6. **Write reviewer notes:** what the app does in two sentences, who uses it (a DTF shop's office and floor),
   each requested scope or role with the feature that needs it, test login and steps, how we meet the data
   rules (retention, encryption, no model training on marketplace data per R15, Etsy: never emailing buyers).
7. **Set a realistic timeline** from the checklist's "Timeline" line: prerequisites (open gaps) + review time + one
   resubmission round. Put the critical path first.
8. **Get the review:** integrations-engineer checks the technical rows, security-reviewer the security rows
   (operating-system "Who reviews whom").
9. **Hand it to the owner** with `send-owner-draft`: what to submit, where, which account, and the
   attachments. Status line becomes `ready for owner — not submitted`.
10. **After the owner submits,** log the date and any reviewer questions in `reviewer-notes.md`. Amazon closes
    a case if you don't answer within 5 days of contact, so draft answers the same day.

## Rules (MUST / MUST NOT)
- MUST NOT submit, register, sign an agreement, create a developer account or answer a reviewer. The owner
  does it (`send-owner-draft`).
- MUST NOT claim a control that is `gap` or unverified. "Not yet, planned by <date>" is an allowed answer; a
  false "yes" is not.
- MUST close every Amazon DPP row before the restricted-role application (`amazon-dpp-evidence-pack`).
- MUST keep the Etsy app name free of "Etsy" and show the Etsy trademark notice (research 10 §3) in the footer
  and connect screen.
- MUST flag a program rule that conflicts with our product (for example Shopify's billing and embedded-app
  rules) to the PM and the owner with `escalate-to-owner`; don't design around it silently.
- MUST use only seeded demo data in screenshots and notes.

## Done when
- `packet.md` has every checklist row as `met` (with evidence you verified), `gap` (owner, backlog id, date)
  or `n/a` (reason), and the date each program page was checked.
- `data-flow.md` and the screenshots exist and match the code today.
- The timeline names the critical path and the earliest honest submit date.
- An `OI-` draft is queued for the owner, and the report lists open gaps.

## References
- [checklists.md](checklists.md): per-marketplace requirements, evidence and timelines
- `invai-docs/research/10-marketplace-engineering-rules.md`, `12-security-quality-playbook.md` §2,
  `04-apis-and-ai-feasibility.md`
- `invai-docs/waves/backlog.md` (B-05, B-06, B-07, B-09, B-10, B-14, B-23, B-28)
- Related playbooks: `amazon-dpp-evidence-pack`, `privacy-request-handling`, `app-store-listing`,
  `security-questionnaire`, `send-owner-draft`, `escalate-to-owner`
