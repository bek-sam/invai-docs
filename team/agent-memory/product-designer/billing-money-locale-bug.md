---
name: billing-money-locale-bug
description: invai-ui Money component uses bare i18n.language, not es-US, causing mixed decimal separators on Spanish billing/digest screens.
metadata:
  type: project
---

`invai-ui/src/app/money.tsx` `<Money>` / `formatMoney` default to `instance.language` (e.g. "es"), which renders "149,00 US$" (comma decimal). The digest pages fixed this with `digestMoneyLang()` in `invai-web/src/components/digest/digest-copy.ts` (maps "es" → "es-US" for money, matching the backend's es-US money/points convention agreed in `specs/weekly-digest.md`). `localeNumber()` in the same file does the same for plain counts.

**Why:** T-23-1's billing page (`invai-web/src/routes/_app/settings/billing.tsx`) fixed counts (orders/credits/users) with `localeNumber` but missed `<Money>` calls (plan price, label fees) — same page then mixes "352 / 10,000" (es-US) next to "149,00 US$" (bare es). Flagged as a blocking finding in `invai-docs/waves/23/reviews/T-23-1-product-designer-r1.md`.

**How to apply:** Any new Spanish-locale screen showing money should use `digestMoneyLang(i18n.language)` (or move that helper somewhere shared/renamed) as the locale passed to `formatMoney`/`<Money>`, not raw `i18n.language`. Worth raising as an `invai-ui` follow-up: `Money` should take an explicit `locale` prop, or default to the es-US convention itself, so every consumer doesn't have to remember this.

**Root cause of a related symptom (T-A6 review, 2026-09-30):** bare `"es"` Intl data has `minimumGroupingDigits: 2`, so a 4-digit amount ("1481,13 US$") silently loses its thousands separator while 5+-digit amounts ("16.468,39 US$") keep it — confirmed with `new Intl.NumberFormat("es", {style:"currency",currency:"USD"}).format(-1481.13)` in plain Node. `es-US`/`es-MX` don't have this quirk but render American-style ("$16,468.39"), not the "period-thousands, comma-decimal, US$ suffix" style the app already uses everywhere. No regional `es-*` variant keeps the suffix style *and* fixes the gap (checked es-AR/CO/UY/CL/PY/BO/VE/DO/GT/HN/NI/PA/CR/PR/GQ — all either go American-style or move `US$` to a prefix).

**Fixed in T-P3-3 (2026-10-01):** `minimumGroupingDigits` turned out to not just be untyped but **unimplemented at runtime** — Node 24.21 / V8 13.6 / ICU 78.3 silently ignores it (absent from `resolvedOptions()`, zero effect on output). `money.tsx` now detects the gap via `formatToParts` (an `integer` part with no sibling `group` part — happens only for exactly-4-digit `es` amounts) and re-groups those digits itself with the locale's own separator, sampled once per cached formatter. `en` and every other digit count take the untouched path. This likely makes `digestMoneyLang()`'s `"es-US"` override (above) redundant — its own doc comment says it exists *because* bare "es" was inconsistent, and that's now fixed at the source — but I didn't touch `invai-web`; flagged as a follow-up in `invai-docs/waves/P3/reports/T-P3-3.md`.
