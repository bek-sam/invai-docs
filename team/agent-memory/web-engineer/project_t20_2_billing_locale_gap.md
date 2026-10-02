---
name: t20-2-billing-locale-gap
description: settings/billing.tsx formats every number with `.toLocaleString()` and no locale (always the runtime default); a wave 20 card scoped away from it left one QA acceptance test red.
metadata:
  type: project
---

`invai-web/src/routes/_app/settings/billing.tsx` calls `.toLocaleString()` with no locale argument at
many sites (plan order/credit limits, AI credit balances, token counts — at least a dozen call sites
as of 2026-09-28), so every number always renders in the runtime's default locale, never the app's
chosen language. Confirmed with `Intl.NumberFormat("es")`/`.toLocaleString()` in this environment:
English happens to match the runtime default, so it looks correct by accident; Spanish always shows
the English grouping ("10,000", never "10.000").

**Why:** T-20-2 (wave 20, gate issue 5) needed "Plan usage renders limits with the locale's thousands
separator." The card's owned paths were `src/components/digest/**`, `src/routes/_app/digests/**`,
`src/routes/_app/settings/notifications.tsx`, `src/lib/errors.ts` (FORBIDDEN case) and one grant in
`src/components/market/recommendation-copy.ts` — `billing.tsx` was never granted, even though QA's own
acceptance e2e (`e2e/digest-dates.spec.ts` AC4) targets `/settings/billing`, not the digest page. Fixed
the same class of bug inside owned files (digest plan-usage numbers, via a new `localeNumber()` helper
in `digest-copy.ts`) and left `billing.tsx` alone per `respect-ownership`.

**Update (round 2, 2026-09-28):** the PM's T-20-1 decision (`reviews/T-20-1-product-manager-r1.md`,
`specs/weekly-digest.md`) settled on **one `es-US` convention for the whole digest** — the digest's
Spanish money and points already render `es-US` (comma grouping), so a bare-`es` `localeNumber()`
("10.000", period) was a mixed-separator bug on the same screen, not a deliberate exception (the
in-code comment claiming an "approved wave-20 exception" was never actually recorded anywhere and was
removed). `localeNumber()` now uses `Intl.NumberFormat(lang.startsWith("es") ? "es-US" : "en-US")`, so
the digest page shows "10,000" / "1,950" in **both** languages. `billing.tsx` still uses bare
`.toLocaleString()` with no locale at all (matches neither convention) and is still out of this card's
owned paths (backlog B-184) — QA's `e2e/digest-dates.spec.ts` AC4 case targeting `/settings/billing`
stays red until that follow-up.

**How to apply:** the next card that touches `billing.tsx` (or extends this one) should replace every
bare `.toLocaleString()` there with a locale-aware call using the app's `i18n.language`, same pattern
as `localeNumber()`. Until then, `e2e/digest-dates.spec.ts`'s AC4 Spanish case
("the same limit shows a period, not a comma") stays red against `/settings/billing`, and this is a
scope gap in the card, not an implementation bug — reported in the T-20-2 task report, not silently
fixed by editing billing.tsx or QA's test.
