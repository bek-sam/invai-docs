---
name: project-t-a7-ops-inventory-today
description: T-A7 (wave A2) build notes - i18n dynamic-key gotchas, app language switching, PageHeader actions overflow at 390px.
metadata:
  type: project
---

Built 2026-09-30, T-A7 (Operations, Inventory health, Today actions panel, designs lifecycle badge).

- `gen-i18n.py`'s `nest()` crashes (`'str' object does not support item assignment`) if one key is both
  a leaf (`"opsV2.driver": "Cut"`) and a prefix of other keys (`"opsV2.driver.channel"`). Keep dynamic
  lookup prefixes distinct from any literal label key at the same dotted path.
- A `t(SOME_MAP[value], value)` call (key looked up via a variable, not a literal `t("key", "default")`)
  is invisible to `extract-i18n.py`'s regex entirely — not even flagged "missing es". It must be hand-added
  to `scripts/i18n-extra-en.json` (both the key and its English default) before `i18n-es-missing.json`
  will ever list it.
- App language is NOT `localStorage["i18nextLng"]`; it's `localStorage["invai.lang"]` (`src/i18n/index.ts`).
  Theme is `localStorage["invai.theme"]` (`"light"|"dark"|"system"`, `src/lib/theme.ts`) — set it, then
  reload/navigate (a full `page.goto` wipes a directly-toggled `.dark` class since `initTheme()` re-reads
  storage on load).
- `@invai/ui`'s `PageHeader` wraps `actions` in a `shrink-0` div; a multi-control actions row (period +
  channel selects + export button) that doesn't fit at 390px gets silently clipped (not scrollable, not
  wrapped), even though `document.scrollWidth === clientWidth` (no real page-level overflow). Confirmed
  pre-existing on the already-reviewed `/analytics/profit` page too — not a regression, a kit gap. Reported
  to product-designer, not fixed locally (not this card's file to patch).
- [[feedback_flatten_chip_text_for_e2e]] and [[feedback_tabs_needs_overflow_wrapper]] remain good patterns;
  this card's `MiniTable` (`src/features/analytics/shared.tsx`) is the new short-list-table pattern, plain
  `<table>` not `DataTable` (which virtualizes, overkill for <20 rows).

Round 2 (reviewer r1 + product-designer r1 fixes, invai-web fdce8c3):
- A backend row shaped `{key, label}` (or `{driver, value, label}`) mixes two very different things under
  `label`: a fixed English sentinel/vocabulary string (`"none"`→"No station", `"in_house"`→"In-house",
  `"unknown"`→"Unknown", the yes/no driver labels) that must be translated by `key`/`value`, vs. a real name
  someone typed (a station or vendor name) that must pass through untouched. Never translate by matching the
  label text itself — key off the enum-ish field, with the raw `label` only as the `t()` fallback so a real
  name still renders when there's no key match.
- A dynamic-key `t(\`ns.driverValue.${driver}.${value}\`, label)` needs its English defaults added to
  `scripts/i18n-extra-en.json` *and* the Spanish in `scripts/i18n-es.json`, same as the single-variable case —
  `pnpm i18n` silently drops any `i18n-es.json` key not also present in the extracted-or-extra set (the
  `{k: es.get(k, flat[k]) for k in flat}` comprehension in `gen-i18n.py` only iterates `flat`).
- Playwright screenshotting this app: the shell's scrollable region is an inner `<main class="flex-1
  overflow-y-auto ...">`, not `document.body` — `page.screenshot({fullPage: true})` and `locator.screenshot()`
  (even after forcing `overflow: visible; height: auto` on `main`) both silently clip to whatever box height
  the flex layout gave `main` at the *current* viewport, cutting off later sections with no error. Fix: measure
  `main.scrollHeight` at a normal viewport, then `page.setViewportSize({height: scrollHeight + margin})` and
  re-screenshot (no style hacks) — this is the only method that reliably got the full page.
- claude-in-chrome's `tabs_context_mcp` blocked immediately with "Multiple Chrome browsers connected, none
  selected" and no way to answer (AskUserQuestion isn't available to this role) — same gap as [[project_t21_5_help_legal_pages]] logged for T-21-5; used `@playwright/test`'s bundled Chromium again. Run screenshot scripts
  *from inside* `invai-web/` (temp `.mjs` file there, deleted after) so Node's ESM resolver finds
  `@playwright/test` in `node_modules` — a script under `/tmp` fails with `ERR_MODULE_NOT_FOUND`.
