# Review of T-7-1 (round 1)

- Reviewer: product-designer on Sonnet 5
- Author: integrations-engineer + web-engineer on Sonnet 5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `invai-web` worktree @`073c53f`: `tsc --noEmit`, `biome check .`, `vite build`, `vitest run` | clean/pass (see reviewer's file for full log) |
| `git diff` of `073c53f` (`routes/_app/shipping.tsx`, `i18n/en.ts`, `i18n/es.ts`) | read in full |
| Live: signed in as `owner@desertbloom.test` on the DB-copy web app (`:5194`/API `:3194`), opened Shipping → Tracking push, clicked "Export tracking for Etsy" once | screenshot before/after; channel picker + button + hint text render correctly; success toast appears; "Tracking uploaded (manual)" badge logic read in `Shipments()` |

## Acceptance criteria (design-relevant slice)
| # | Met? | Evidence |
|---|---|---|
| 3. "Export tracking for `<channel>`" button, count, download, short en/es instructions | **No** | Button, channel picker, count and download all work and read well in English. Two of the four per-channel instruction strings are not translated into Spanish (see blocking finding). |

## Blocking findings
1. `invai-web/src/i18n/es.ts:1471-1480` (`shipping.exportWhere.amazon`, `shipping.exportWhere.tiktok`) — raw, untranslated English shipped under the Spanish locale. Compare to `en.ts`: the Amazon and TikTok strings are character-for-character identical in both files, while the Etsy and Walmart strings in the same object were properly translated. Failure scenario: a Spanish-locale shop owner (the persona this card explicitly calls out — "Short instructions (en/es)") picks Amazon or TikTok Shop from the export dropdown and reads an English paragraph ("Amazon: Seller Central → Orders → Upload Order Related Files → Shipping Confirmation.") with no translation at all — not even the surrounding sentence structure, just the raw English string. This is exactly the kind of half-finished localization that's worse than a fallback, because it looks intentional. Fix: translate the two remaining hints the way Etsy/Walmart's were done (keep literal marketplace UI labels like "Seller Central" untranslated where that matches the target site's own UI language, but translate the connecting words: "→ Subir archivos relacionados con pedidos → Confirmación de envío", etc.).

## Checks
- [x] Only owned paths changed (`i18n/{en,es}.ts` new keys, `routes/_app/shipping.tsx` export button only).
- [x] Nothing outside scope.
- [x] No weakened tests (scan script: no hits inside this commit's own files).
- [x] Accessibility: the channel `<select>` has `aria-label`, the button has a text label plus icon (not icon-only), a loading spinner replaces the icon while pending, the hint text is plain paragraph copy below the control (not color-only signaling) — reasonable for a first pass. Did not run a full WCAG sweep (out of scope for this card; T-7-5 owns the accessibility sweep this wave).
- [ ] en/es text: two hints are raw English — blocking, see above.
- [x] Copy tone matches the rest of the app (plain, instructional, no jargon beyond what the marketplace itself uses).

## Optional notes (not blocking)
- Success toast: `t("ship.exportDone", "{{n}} shipments exported for {{channel}}", ...)` doesn't pluralize — "1 shipments exported for Etsy" reads oddly. Minor; recommend `_one`/`_other` i18next keys or an inline conditional when the author does the next pass.
- The "Tracking uploaded (manual)" badge (Shipments tab) is a good, honest label — it doesn't imply the tracking was actually pushed anywhere, which matches how these four channels really work.
- Layout: the export control is a plain bordered box above the existing "Tracking push" table; visually distinct enough, no complaint.
