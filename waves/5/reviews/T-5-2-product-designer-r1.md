# Review of T-5-2 (round 1)

- Reviewer: product-designer on Sonnet 5
- Author: web-engineer on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| Same worktree/live-stack setup as the `reviewer` file (`invai-web` @ `a2566b2`, backend HEAD `72c1139` on :3192, web on :5192, DB copy `invai_t52_review`, Redis db 10) | reused, not duplicated here |
| Browser pass: Channels (OAuth success/error, CSV import, stock-push toggle, connection health), Shipping settings, Shipping → Shipments void dialog (code + screenshot) | see below |
| i18n key-parity check (1381/1381, no gaps) and raw-English JSX grep (no hits) | same as `reviewer` file |
| Read 3 of the author's screenshots: `void-pushed-en.png`, `channels-issues-en.png`, `shipsettings-es-dark.png` | all match the live behavior and the code |

## Acceptance criteria (design lens)
| # | Met? | Evidence |
|---|---|---|
| 1. OAuth return states | Yes | The success and error banners read as calm, specific system status, not raw error text — "The Shopify approval link expired before it was finished. Connect the store again." names the problem and the next step in one sentence. Dismiss clears the URL params too, so a refresh doesn't re-show a stale banner. Good pattern. |
| 2. Import history, health, stock opt-in | Yes | The stock-push explanation ("on hand minus reserved · within 30 s · next change · mapped listings only") is the right amount of detail directly under the switch, not hidden in a tooltip — matches `write-plain-language-copy` norms. Health issues use a two-tier disclosure: one plain-language line up front, a collapsed `<details>`/"Details" for the raw text underneath — good default for staff who don't need the raw string but shouldn't lose it. The "Needs attention" badge triggering on any explained issue (not just `health.ok === false`) is the right call; a store can be "ok" by the API's flag and still need a human. |
| 3. Shipping settings | Yes | Field labels are fully translated and unit-suffixed consistently (`Length (in)`, `Empty weight (oz)`) instead of the old bare `L (in)`. "ZPL — coming soon" is honest about a real limitation instead of hiding the option or silently no-op'ing it. Test-mode vs Live is a clear badge next to the carrier account, exactly where someone would look before trusting a rate. |
| 4. Void confirm, T-2-5 rules | Yes | The dialog is well-ordered: title asks the yes/no question, body states the one irreversible fact ("You can't undo it from here"), then three bullets carry the conditional rules (refund-pending, scan cutoff + CSV exception, already-pushed cutoff) so the common case isn't buried under edge cases. The already-pushed state swaps the primary action from "Void label" (destructive) to "Got it" and adds a red inline alert instead of letting someone click a button that will just fail — this avoids a dead-end error round-trip. Confirmed against `void-pushed-en.png`: text matches the code exactly, `role="alert"` present on the red banner. |
| 5. en/es, 390 px, keyboard | Yes | `shipsettings-es-dark.png` shows the Spanish copy is genuinely translated (not machine-literal — "Ajustes de envío", "Paquetes de prueba" region reads naturally) and dark mode contrast looks fine on the fields and badges. The weight-per-style row fix (`grid-cols-[minmax(0,1fr)_6rem_auto]` + `min-w-0`) is the correct technique for a 390 px target — clamp the flexible column, fix the numeric/icon columns, rather than shrinking text. Icon-only buttons (dismiss, settings, disconnect, remove-preset, remove-weight-row) all carry descriptive translated `aria-label`s that include the entity name where useful ("Settings for {{name}}", "Remove style {{code}}") rather than a generic "Delete" — good for anyone using a screen reader across a list of several similar rows. |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed — see the `reviewer` file's note on `nav.ts`/`routeTree.gen.ts`; from a design/IA standpoint the one `nav.ts` line is the correct placement (under Settings, `Truck` icon, gated on `shipping.manage`, keywords consistent with the Channels entry above it) and doesn't reorder or touch any other entry, so I have no IA objection to it landing this way.
- [x] Nothing outside scope
- [x] Tests exercise the behavior, none weakened
- [x] Tenancy, idempotency, money in cents, en/es text — en/es confirmed; no backend/money code in this diff
- [x] Decisions recorded where needed — none needed

## Optional notes (not blocking)
1. **Pre-existing gap, already logged to me in the report:** `@invai/ui`'s `RelativeTime` shows English ("6 hours ago") on Spanish screens (e.g. "last import 6 hours ago" under a Spanish-language connection card). Not introduced by this card. I'll pick this up as a follow-up on `invai-ui` rather than blocking T-5-2 on it.
2. The CSV-connection empty state ("No CSV imports yet. Import a file and it shows up here.") is a nice concrete instruction rather than a bare "No data" — worth keeping as the house style for other empty states in the wave.
3. Minor, non-blocking polish idea for later: in the void dialog, the three rule bullets are always shown regardless of channel — for a CSV-only order the "tracking is sent to the buyer's channel" bullet never applies (CSV never pushes tracking). Not worth the added conditional complexity for round 1, but worth a look if the dialog gets revisited.
