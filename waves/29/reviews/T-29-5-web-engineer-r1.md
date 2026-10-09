# T-29-5 review r1: web-engineer (consumer co-review)
Reviewer: web-engineer. Author: contract card (architect). Verdict: **approve**

Change: invai-contracts dc62328..0f666f1 appends "purged" to ItemArtworkSummary.status (and ITEM_ARTWORK_STATUSES), version 0.14.0. Additive, enum value last.

Evidence I re-ran:
- invai-web `pnpm typecheck`: clean (tsc --noEmit, no errors).
- invai-floor `pnpm typecheck`: clean.
- grep of artwork status use in invai-web/src, invai-floor/src, invai-ui/src:
  - order-detail.tsx:328-347: label via `t("artworkStatus.${status}")`; purged gets en "Removed for privacy" / es "Eliminado por privacidad" (i18n/en.ts:179, es.ts:183); no icon (only flagged/approved have one); approve button only for flagged/rendered, so purged offers no action.
  - personalization.index.tsx:144: filter dropdown maps ITEM_ARTWORK_STATUSES, so "purged" appears with label and `counts[s] ?? 0` (safe if the API omits it); default filter stays "flagged".
  - personalization.index.tsx:217: badge tone is warning for flagged/failed, success for approved, else secondary, so purged is neutral grey. Sensible (not an alarm, not a success).
  - No exhaustive switch or Record<ArtworkStatus,...> in web, floor or ui; floor has no artwork status use.
- markdown.ai.test.ts:107-111 already asserts both catalogs carry purged (T-29-3).

Blocking findings: none.
Optional note: an old web build receiving "purged" would show the raw key as fallback text only; the `t(key, status)` default covers it.
Not run: browser/screenshots (owner rule 0024); no web tests re-run (no web code changed in this card).
