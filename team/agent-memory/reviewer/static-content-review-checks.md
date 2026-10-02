---
name: static-content-review-checks
description: Reviewing invai-web public markdown/help/legal pages — XSS probe via renderToStaticMarkup, no-API proof, overflow and list-marker checks, sandbox limits
metadata:
  type: feedback
---

2026-09-29 T-21-5: for a hand-rolled markdown renderer, prove "no raw HTML" with a temporary vitest file in `src/content/` (vitest include is `src/**/*.test.ts`; environment node) that renders `MarkdownBlocks` via `react-dom/server` `renderToStaticMarkup` and writes the HTML to the scratchpad (console.log is swallowed). Delete it at once. React 19.3 rewrites `javascript:` hrefs itself, but `data:`/`vbscript:` pass through, so check for a scheme allowlist.

**Why:** "never uses dangerouslySetInnerHTML" is the author's claim; the escaped output is the proof.

**How to apply:**
- Prove public routes call no API by building with `VITE_API_URL=http://localhost:3999` (nothing listening). Then any request to a non-preview origin in Playwright is a finding.
- Measure `scrollWidth > innerWidth` at 390. Long inline `code` spans overflow.
- `li` with `flex` hides ordered-list numbers. Look at the builder's screenshots for missing step numbers.
- Probing Valkey DB sizes (`valkey-cli dbsize`) was refused by the auto-mode classifier. For a signed-in UI check without the shared API, fall back to code reading and say so in the review. See [[env-web-review]].
