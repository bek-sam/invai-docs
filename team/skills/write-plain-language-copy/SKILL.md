---
name: write-plain-language-copy
description: Write InvAI user-facing text in plain shop language, in English and real Spanish, using the shop words (order, blank, gang sheet, press, pack station, label) and the i18n files each app really uses. Use for any UI string, error, empty state, floor message, email, help article, owner report or inbox entry, or when someone says "copy", "wording", "translate" or "Spanish".
---

# Write plain-language copy

Every word a shop owner, office person or presser reads says what happened and what to do next, in short
sentences, in English and Spanish.

## When to use
- Any new or changed UI string (web, floor, shared UI), error message, empty state or toast.
- Emails, packing slips, label and PDF text.
- Help articles (`invai-docs/help/{en,es}/`), owner reports and `owner-inbox.md` entries.

## Steps
1. **Know the reader.**
   - Owner or office (web): busy, at a desk, knows their shop, not our internals.
   - Presser, packer, receiver (floor tablet): standing, gloves on, noisy room, often Spanish first. Two to
     six words, big and unambiguous.
   - Vendor (vendor portal): a print shop outside the company.
2. **Write the English first.** For each message:
   - **What happened**, in the shop's words (`glossary.md`).
   - **What to do next**, as a verb ("Scan the blank", "Map this SKU", "Try again in a minute").
   - Numbers the person needs (order number, count, time left), never internal ids.
   - Sentences under about 15 words. Active voice. No blame.
3. **Errors map from codes.** Backend errors come as typed oRPC codes (`invai-backend/src/lib/errors.ts`); the
   app maps each code to a translated message. Never show a raw code, stack trace or English-only server text.
4. **Floor messages block clearly.** A mismatch message names the problem and the fix: "Wrong size. Scan an M
   blank." A blocking result must look and sound different from success (`build-floor-flow`).
5. **Write the Spanish.** Natural Mexican/US Spanish as the catalogs use it (tú form: "Escanea", "Revisa").
   Use the glossary words. Translate meaning, not word by word. Keep placeholders exactly (`{{orderNo}}`,
   `{{n}}`, `{{count}}`).
6. **Put it where the app reads it.**
   | App | How strings work | Files |
   |---|---|---|
   | invai-web | Write `t("area.key", "English default")` in your component, then run `pnpm i18n` (runs `scripts/gen-i18n.py`, then formats). Spanish goes in `scripts/i18n-es.json`; missing ones are written to `scripts/i18n-es-missing.json` | generated `src/i18n/en.ts`, `src/i18n/es.ts` (don't hand-edit) |
   | invai-floor | Edit both catalogs by hand; `es.ts` is typed `FloorStrings` from `en.ts`, so a missing key fails `pnpm typecheck` | `src/i18n/en.ts`, `src/i18n/es.ts` |
   | invai-ui | Shared component strings | `src/i18n/locales/` |
   | help center | One file per article per language | `invai-docs/help/en/`, `invai-docs/help/es/` |
7. **Check it on screen.** Run the app, switch to Spanish, take screenshots of the new text at 390 px (web)
   and 1280×800 (floor). Spanish runs 20–30% longer: look for truncation and wrapping. Check that no raw key
   (`orders.shipBy`) or English fallback shows.
8. **Money, dates, sizes.** Format through `Intl` with the active locale. Cents → currency, never "$12.5".
   Sizes in inches as given, never rounded ("10.5 × 12 in").

## Rules
- MUST ship English and Spanish together. No "TODO translate".
- MUST use the glossary words. A new shop word needs the product-designer's OK and a glossary line (through
  the tech lead).
- MUST NOT use internal words in UI copy (tenant, RLS, job, queue, webhook, payload, mock). See `glossary.md`.
- MUST NOT put buyer PII in logs, error text, analytics or AI prompts through copy templates.
- MUST NOT make claims in public or legal text (pricing, compliance, "secure", "guaranteed") without
  `compliance-officer` review; outbound text goes through `send-owner-draft`.
- MUST keep floor tap targets and text large: copy that forces a button to wrap is a bug.

## Done when
- Every new string exists in English and Spanish in the right file for its app, and `pnpm typecheck` passes
  (floor catches missing keys).
- For web: `pnpm i18n` ran and `scripts/i18n-es-missing.json` is absent, or has none of your keys (the script
  writes it only when a Spanish string is missing).
- Screenshots in both languages were looked at, with no truncation, raw keys or English fallbacks.
- Each error or block message says what happened and what to do.

## References
- `glossary.md` (this folder): shop words en → es, words to avoid
- `invai-docs/research/01-shop-workflow.md` (how shops talk about their work)
- `invai-docs/research/12-security-quality-playbook.md` §3.8 (i18n rules)
- `CLAUDE.md` (Conventions: plain language, English and Spanish)
- Related: `build-dashboard-screen`, `build-floor-flow`, `write-help-article`
