---
name: project_t_p4_3_spanish_sweep
description: T-P4-3 Spanish pass of /catalog/designs + billing.tsx — screenshot scroll gotcha and a bug class (English literal wrapped around already-localized numbers)
metadata:
  type: project
---

T-P4-3 (wave P4) found and fixed on a manual Spanish pass of `/catalog/designs` (list + detail) and
`settings/billing.tsx`: `action.loadMore` had no i18n key at all (rendered the literal key); `SignedImage
alt={p.placement}` used the raw enum instead of a translated label; billing's credit-history table wrapped
two already-`localeNumber()`-formatted numbers in a hardcoded English `" in / ... out"` literal — a bug class
worth re-checking elsewhere: a field being correctly localized doesn't mean the surrounding sentence is.

**Why:** `t("key")` with no default value renders the literal key string when the key is missing — a visible,
silent leak in both en and es, not just es; always grep the key exists in en.ts (or give a default) before
assuming a missing-Spanish-only bug. Separately, `localeNumber()`/`formatMoney()` calls are easy to spot-check
but the English words stitched around them (as in `{{n}} in / {{n}} out`) are easy to miss on an en-only read.

**How to apply:** on any Spanish-screen sweep, also search owned files for template-literal-looking
concatenation around `localeNumber(`/`formatMoney(`/`Money` calls, not just raw `"..."` strings outside `t()`.
For Playwright screenshots in this app: `page.screenshot({ fullPage: true })` does NOT capture past the
viewport — the scrollable element is `<main class="flex-1 overflow-y-auto ...">`, not `document.body`/window.
Scroll it explicitly (`document.querySelector("main")?.scrollTo(0, 999999)`) and take a second screenshot to
check the bottom of a long screen for clipping; `fullPage: true` alone silently crops it to viewport height.
Confirms prior entry [[feedback_login_resets_locale_from_session]] and
[[project_t23_1_p2_sweep]]'s MinIO/CSP note (still not a bug in 2026-10).
