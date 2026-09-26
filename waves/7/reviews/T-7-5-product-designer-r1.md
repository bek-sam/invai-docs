# Review of T-7-5 (round 1)

- Reviewer: product-designer on Sonnet 5
- Author: web-engineer on Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| Read `git show 6aa9b99`, `c29c60a` (`invai-ui`) and `74fa8b4` (`invai-web`) in full | reviewed alongside the reviewer's re-run of tsc/biome/vitest/build (both clean; see `T-7-5-reviewer-r1.md`) — not re-run a second time here, per the token budget |
| OKLCH→sRGB→WCAG contrast check on `--color-success`/`--color-success-foreground` (badge pairing) and on bare `text-success` against `--color-background` | light badge 3.49:1→4.83:1, dark badge ~7.23:1 unchanged; light `text-success`-on-background 3.70:1→5.11:1, dark 7.06:1 — all four pass AA's 4.5:1 |
| Grep of every `text-success`/`bg-success` consumer in `invai-ui`/`invai-web` (`stat-card.tsx`, `money.tsx`, `station-header.tsx`, badges, order-detail checkmarks, checklist, billing credits column, stock deltas, etc.) | one shared token, ~20 call sites; all get the same contrast improvement, no call site needed its own change |
| Grep for `gang sheet`/`Hojas de prensado`/`mock`/`sandbox`/`entorno de prueba` across `invai-ui` and `invai-web`'s locale files | see finding below |
| Traced the 4 toast-suppressed codes against their dialog hosts (`UpgradePromptHost`, `VerifyEmailPromptHost`) and where each host mounts | both mount unconditionally in the `_app` layout — no route exists where the toast is gone and no dialog can appear |
| Read the `TabsTrigger` and `Progress` diffs (`c29c60a`) for behavioral correctness (not just axe-compliance) | see Checks |

## Acceptance criteria (design-relevant slice)
| # | Met? | Evidence |
|---|---|---|
| 1. Table rows keyboard-reachable with an accessible name that matches what's shown | Yes | Accessible name is generated from the visible cell text itself (product name, PO number, sheet name, etc.) rather than a separate hand-written label — so it can't drift out of sync with what's on screen, and a screen-reader user hears the same identifying text a sighted user reads. Focus ring (`focus-visible:ring-2 ring-inset`) is visible and consistent with the rest of the design system's focus treatment. |
| 3. Locale formatting | Yes | `formatRelativeTime(..., "es")` produces the exact AC example, "hace 4 semanas," and the future-tense case reads naturally ("dentro de 3 horas") rather than a stilted literal translation — good, idiomatic Spanish RelativeTimeFormat output, not custom copy that could go stale. |
| 4. No English left, untranslated Spanish fixed | Mostly, one consistency gap (not blocking) | `channels.mock` ("sandbox" → "entorno de prueba") is a clean fix and improves comprehension for a Spanish-reading owner deciding whether a channel is live. `nav.gangSheets` ("Gang sheets" → "Hojas de prensado") satisfies the letter of AC4 (the two strings were identical, which is exactly what the AC calls out) but see the finding below — it now disagrees with how "gang sheets" reads everywhere else in the Spanish app. |
| 5. Toast suppressed only where a dialog already explains | Yes | Confirmed no dead end: every one of the four suppressed codes still gets a clear, actionable dialog (upgrade/billing CTA or "confirm your email" with a resend button) wherever in the app the error can occur, since both hosts are mounted at the layout level rather than per-page. A user who trips `PAYMENT_REQUIRED` on, say, a label-buy action deep in Order detail still sees the explanation — nothing silently fails. |
| 6. Axe: 0 serious/critical | Trusted per the reviewer's re-derivation of the contrast math; not re-run live. |

## Blocking findings
None.

## Checks
- [x] Copy quality: new en/es strings (`common.skipToContent`, `dataTable.emptyTitle`, `appShell.expandSidebar`/`collapseSidebar`, `command.menuTitle`/`searchCommands`, `pinPad.clear`/`backspace`, `errors.generic`/`network`/`notImplemented`) are plain, short, and match the existing tone elsewhere in the app (verified against sibling keys in the same files). No jargon introduced.
- [x] Visual/interaction correctness beyond axe-compliance:
  - `TabsTrigger`'s `aria-controls` fix is behaviorally sound for the segmented-filter-tab pattern (Orders' "Todos"/"Needs mapping"/etc.): those tabs never had a real panel to point at, so dropping the attribute is the honest fix rather than papering over it with a fake empty panel. Pages that do pair `Trigger`+`Content` (Shipping, SKU mapping) keep a valid reference on the active tab, so nothing changes for a screen-reader user navigating those.
  - `Progress`'s `aria-label` fallback (`"{{value}}%"`) is a sane default for an unlabeled progress bar (e.g. the onboarding checklist), and callers with something more specific to say (e.g. "3 of 5 steps complete") still win, since the fallback only applies when no `aria-label`/`aria-labelledby` was passed.
  - The success-color darkening (`oklch(0.6 0.15 150)` → `oklch(0.52 0.15 150)`) keeps hue and chroma fixed, so it still reads unambiguously as "success green" rather than shifting toward a muddier or different-feeling color — a reasonable token-level fix that improves every consumer (badges, checkmarks, stat deltas, station-online indicator) at once rather than patching each call site.
- [x] Terminology consistency (finding, not blocking): `nav.gangSheets` now reads "Hojas de prensado" in `invai-web`'s sidebar, matching `invai-ui`'s own nav key — but `invai-web`'s `es.ts` still uses the untranslated loanword "gang sheets" in about a dozen other visible strings (the signup subtitle, the vendor-invite subtitle, the sheet-builder title, the sheet preview alt text, the vendor-inbox subtitle, the channel-settings copy). A Spanish-reading owner will see "Hojas de prensado" in the sidebar and "gang sheets" everywhere they click into — the same object called two different things in the same session. Recommend a follow-up card (not blocking this one, since AC4's literal ask — fix the identical-value pair — was met) to pick one term for "gang sheet" in Spanish and sweep every occurrence in `invai-web`'s `es.ts` to match.
- [x] No dark patterns or a11y regressions introduced by the toast suppression: nothing is silently swallowed; each suppressed code still has a clear, reachable explanation.

## Optional notes (not blocking)
- The DataTable activator button's hit area (`-m-3 w-[calc(100%+1.5rem)]`) correctly recreates the full original cell as the click/tap target, so touch-target size for mobile/tablet views of these tables isn't reduced by the a11y fix — worth calling out since a common regression in this kind of change is an accidentally-shrunk clickable area.
- Agree with the reviewer's flag that AC1's fix doesn't reach `orders-table.tsx` (the Orders page's own non-`DataTable` table) — that page is InvAI's highest-traffic table for the office role, so I'd prioritize a follow-up card for it over the terminology sweep above.
