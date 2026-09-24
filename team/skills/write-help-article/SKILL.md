---
name: write-help-article
description: Write an InvAI help-center article in English and Spanish, symptom-first, in shop words, with steps and screenshots checked against the running app. Use when a support ticket shows a training gap, a feature lands that shops will use, onboarding needs a guide, or someone asks for "help doc", "how-to" or "artículo de ayuda".
---

# Write a help article

A shop owner, office worker or Spanish-reading presser finds the article by the problem they see, and fixes it
in a few steps that match the screen in front of them.

## When to use
- `triage-support-ticket` classed a ticket as "needs training".
- A self-serve onboarding step in `onboard-shop` has no article.
- A feature landed that changes what shops see (with `release-notes`).
- A usability session or audit found a step people can't figure out and the fix is words, not code.

## Steps
1. **Name the reader and the moment.** Role (owner, office, designer, presser, packer, receiver, vendor),
   device (desktop, phone, 10-inch tablet in gloves), and what they were trying to do. Floor articles are read
   on the tablet, often in Spanish.
2. **Write the title as the symptom** in the reader's words, the way the ticket said it: "My order says Needs
   mapping", "The press screen went red", "Some rows failed when I imported my Etsy CSV". Task articles use
   the goal: "Pair a new tablet". Not feature names.
3. **Check it's not a duplicate:** `ls invai-docs/help/en/ invai-docs/help/es/` and grep for the symptom.
   Update the existing article rather than adding a second.
4. **Walk it in the running app** as that role, on the seed shop (Desert Bloom Tees; logins and PINs in
   `CLAUDE.md`). Use a stack someone already has running, or your own on a separate port; don't restart shared
   processes. Copy every screen name, button and message **exactly** from the app, in both languages:
   - web: `invai-web/src/i18n/en.ts` and `es.ts`; screen names in `invai-web/src/lib/nav.ts`,
   - floor: `invai-floor/src/i18n/en.ts` and `es.ts`,
   - error and flag codes the reader might see: `MISMATCH_REASONS` and `REPRINT_REASONS` in
     `invai-contracts/src/schemas/production.ts`, item states in `invai-contracts/src/states.ts`.
5. **Take screenshots** of the key step at the reader's viewport (web 1440 or 390, floor 1280×800), in each
   language, with `.claude/skills/ux-audit/shoot.mjs`. Save them to `invai-docs/help/img/<slug>/`. Seed data
   only; crop anything that looks like a real address.
6. **Write the English article** from `template.md`: symptom, why it happens (one or two lines), fix steps
   (numbered, one action each), how to check it worked, and "still stuck?" (what to send support, and when to
   stop and ask).
7. **Write the Spanish article** as a real Spanish text, not a word-for-word translation. Use the app's own
   `es` labels, `usted`, and short sentences. Keep shop words consistent with the app: check the `es` strings
   for "gang sheet", "blank" and "transfer" before choosing your own. Same slug, same screenshots in Spanish.
8. **Cross-link:** from the macro in `invai-docs/customers/macros/` that answers this ticket, and from any
   onboarding checklist step it serves (tell customer-success the path).
9. **Get the review:** one domain owner (the engineer or designer who owns that screen) confirms the steps
   match the code. A claim about marketplace rules, AI or privacy also goes to the compliance-officer.
10. **Publishing goes through the owner.** Until a public help center exists, articles live in
    `invai-docs/help/` and reach shops as links or pasted text in owner-sent replies (`send-owner-draft`).

## Rules
- MUST start with the symptom the reader sees, and put the fix in the first screen of text.
- MUST verify every label, path and step against the running app and the i18n files. When the code and the
  article disagree, the code wins. If the code looks wrong, file it through `triage-support-ticket`.
- MUST ship en and es together, with the same steps and the same screenshots in each language.
- MUST say when to stop and contact support (for example, anything that risks a wrong press or a missed
  ship-by).
- MUST NOT document a bug as intended behavior, or a workaround as the normal way.
- MUST NOT include real shop, staff or buyer data in text or images.
- MUST NOT promise features or dates.

## Done when
- `invai-docs/help/en/<slug>.md` and `invai-docs/help/es/<slug>.md` exist with matching structure, and
  screenshots in `help/img/<slug>/`.
- Every UI label in the article matches the i18n files (list the keys you checked in your report).
- A domain owner reviewed it; linked from the macro or onboarding step.

## References
- `template.md` (this folder)
- `.claude/agents/docs-writer.md`
- KCS-style structure, issue in the requester's words, "escalate when": [KCS article
  structure](https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Practices_Guide/030/040/010/020),
  [Document360 troubleshooting articles](https://docs.document360.com/docs/troubleshooting-articles) (checked
  2026-09-24)
- Related playbooks: `write-plain-language-copy`, `triage-support-ticket`, `release-notes`, `ux-audit`
