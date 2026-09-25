# Review of T-5-1 (round 1)

- Reviewer: product-designer (co-review) on Sonnet 5
- Author: web-engineer + backend-engineer (orders) on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| Read `es-02-address-hold-form.png`, `es-04-void-confirm.png`, `en-03-bulk-cancel-confirm.png` (3 of the author's screenshots, per token budget) | see notes below |
| `git -C invai-web diff bca872f^ bca872f -- src/i18n/en.ts src/i18n/es.ts` (key-name diff) | 110 keys added on each side, identical key set |
| `grep` for raw JSX text / hardcoded strings in `order-actions.tsx`, `dialogs.tsx`, `routes/_app/orders/index.tsx` | every hit is a `t(key, "English default")` call, not a bare string node |
| Read `order-actions.tsx` for `can(...)` gates on the address form, unit actions and void | present (see reviewer's file for the exact grep) |

I did not stand up my own browser session for this co-review — the reviewer's file already exercised every flow against the API and the shared Chrome session was contended by a concurrent review; I focused this pass on the 3 screenshots plus the copy/i18n/state-coverage claims in the diff, which is what a UI co-review adds on top of the functional review.

## Acceptance criteria (design-relevant slice)
| # | Met? | Evidence |
|---|---|---|
| 1 Flag messages translated from codes | Yes | Backend now stores a translated message per flag code (confirmed in reviewer's curl: posting a flag with a custom `message` came back with the code's canonical translated text, "manual review", not the raw input) — the UI can't drift from server copy. |
| 2 Void confirmation dialog | Yes | `es-04-void-confirm.png`: "¿Anular esta etiqueta?" explains the refund timing and "no envíes el paquete" warning before the destructive action, Cancelar/Anular etiqueta both present and the destructive one is styled distinctly (red). Matches the card's ask for reject/busy/refund-pending copy (report also lists this explicitly). |
| 3 Address hold form, no implied carrier check | Yes | `es-02-address-hold-form.png`: banner text is careful — "la espera se quita cuando la calle, la ciudad y el código postal se ven bien" (format-only, no carrier promise). The help text under the Save button repeats this: "La paquetería revisa la dirección cuando compras la etiqueta" — correctly defers the real check to buy-time, matching the card's explicit instruction not to imply a carrier-verified check. |
| 4 Bulk cancel confirmation | Yes | `en-03-bulk-cancel-confirm.png`: "Cancel 2 order(s)?" states the irreversible consequences plainly (units cancelled, sheeted transfers marked scrap, blanks returned, unshipped labels voided, "This can't be undone"), requires a Reason, has a Back path. Good destructive-action pattern, consistent with the void dialog's. |
| 5 en/es parity, keyboard, states | Yes (parity); not independently re-screenshotted | en/es key sets are 1:1 by name (110/110). Every screenshot reviewed uses full, natural Spanish (not machine-literal) — "Guardar y quitar espera", "Anular etiqueta" read like a native copywriter, not a string-for-string translation. |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed — n/a to this co-review's focus (reviewer confirmed `git diff --stat`).
- [x] Nothing outside scope
- [x] Tests exercise the behavior — n/a (functional review's job); no UI test weakening spotted in `views.test.ts`'s diff.
- [x] Tenancy / idempotency / money / en-es text — en/es text confirmed at parity; the rest is the primary reviewer's checklist.
- [x] Decisions recorded where needed — the report's "Pre-existing, not in my paths" section correctly separates this card's copy from known pre-existing gaps (English relative timestamps, English timeline text, "Etiqueta" ambiguity) instead of silently absorbing them into scope.

## Optional notes (not blocking)
- The report flags "Etiqueta" being used for both order tags and shipping labels in Spanish as a pre-existing ambiguity for product-designer to decide. Agreed this is worth resolving, but it's a catalog-wide term already in use before this card, not something `bca872f` introduced — deferring to a dedicated i18n glossary pass rather than blocking this card on it.
- I didn't get an independent look at the 390px/keyboard/loading-state screenshots beyond the 3 I read (token budget caps co-reviewers at 3). Nothing in the 3 I saw raises a concern; if a future round wants the full 390px set re-checked, that's a fast follow, not a blocker here.
