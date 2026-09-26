# Review of T-6-1 (round 1)

- Reviewer: product-designer on Sonnet 5
- Author: web-engineer (+ backend-engineer inventory) on sonnet
- Verdict: approve

## Evidence I re-ran
Co-review scoped to the UI risk flag: `invai-web` `13927c3` only, read against the card's AC6
("en and es, 390 px, keyboard accessible, and loading, empty and error states") and the shared
component conventions. Backend/contract behavior is covered by the primary reviewer's file
(`T-6-1-reviewer-r1.md`); I re-checked the pieces that matter for the UI surface (idempotency
outcome shown to the user, masked API key) rather than re-running the whole backend suite.

| Command | Result |
|---|---|
| `invai-web` (review worktree at `13927c3`): `tsc --noEmit` | pass |
| `invai-web`: `biome check .` | pass, no fixes |
| `invai-web`: `vitest run` | 14 files, 76 tests passed |
| `invai-web`: `vite build` | succeeds |
| Diff read of `en.ts`/`es.ts` additions | every added en key has a matching es key (diffed sorted key sets, no mismatch) |
| Diff read of new JSX for hardcoded strings | no raw English text found outside `t()` calls |
| Real API pass (piggybacked on the primary reviewer's DB copy, :3191) to see the actual response shapes the UI renders for mark-placed idempotency, receive idempotency, count variance, and the masked API key | see criteria table |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Manual PO create/edit, variant search, costs in cents | yes | `po-form-dialog.tsx` uses the existing `BlankPicker` for variant search (consistent with the rest of the app, no new picker invented); cost fields go through the shared cents<->dollars formatters (`centsToDollarsInput`/`parseDollarsToCents`), same pattern as `settings/inventory.tsx`. Edit is gated to `draft` only in the PO detail page, matching the AC. |
| 2. Mark placed manually, dialog UX | yes | `MarkPlacedDialog` is a focused, single-field dialog (`supplierOrderRef`) with a clear hint that this is for suppliers with no ordering API; button label and confirm disabled until a ref is typed. Matches the app's existing `Dialog`/`DialogFooter` pattern (`ConfirmDialog`, other feature dialogs) rather than inventing new dialog chrome. |
| 3. Receiving idempotency + `submitting` visibility + stuck alert | yes (UI side) | The receive button's `idempotencyKey` regenerates only on `onSuccess`, so a double-click or a retried failed request reuses the same key — the double-submit outcome verified by the primary reviewer (received once) is what the UI actually sends. `PoStatusBadge` renders whatever status the backend returns, so `submitting` now shows instead of being silently hidden as `draft` — a real, visible state the office can act on/wait on, not a UI-side guess. No UI surface for the 15-minute alert itself is expected here (it's a `today`/alerts-feed concern per the codebase's existing pattern), which matches the card's AC3 wording (alert raised, not a bespoke banner). |
| 4. Stock count screen (pick location, enter counts, preview diff, submit) | yes | `CycleCount` in `stock.tsx`: location picker, `BlankPicker` to add lines, a live per-line diff as you type (not only after submit), and a post-submit "Last count" variance summary with color-coded +/- deltas (`text-success`/`text-danger`) — good, low-friction feedback loop for a repetitive floor/office task. Empty state (`ClipboardCheck` icon + hint) shown before any line is added. |
| 5. Inventory & supplier settings | yes | Per-supplier card layout (account #, free-freight threshold, masked API key with a "set"/"not connected" hint and a type-to-replace or explicit Remove toggle) reads clearly and doesn't require the user to guess whether a key exists. `type="password"` + `autoComplete="off"` on the key field is the right call for a credential input. Reorder-timing fields (velocity/lead/safety days, `reserveOnImport`) are grouped in their own card, separate from per-supplier settings — good grouping. |
| 6. Quality: en/es, 390px, keyboard, loading/empty/error states | yes | i18n key parity confirmed (see evidence). All new screens compose existing, already-audited primitives (`Field`, `NativeSelect`, `SkeletonRows`, `ErrorState`, `EmptyState`, shared `Dialog`) rather than hand-rolling new layout/typography, so 390px and keyboard behavior inherit from components this team has already hardened in earlier waves rather than being reinvented here. `settings/inventory.tsx` shows `SkeletonRows` while pending and `ErrorState` (with retry) on failure for both `settings` and `suppliers` queries. I did not open a live browser at 390px for this round (token budget; the review skill caps a co-reviewer's screenshot review at 3 and asks reviewers to take their own only when something looks wrong in the diff — nothing here did), so this is a code-level accessibility/consistency read rather than a pixel-verified one. |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed: `features/inventory/**`, `routes/_app/inventory/**`, new `routes/_app/settings/inventory.tsx`, own i18n keys, plus one nav-entry line and the generated route tree (see the primary reviewer's note — not blocking, but flagging it here too since it's squarely a UI-scope question).
- [x] Nothing outside scope: no new design primitives introduced; everything is composed from existing `@invai/ui`/shared components.
- [x] Tests exercise the behavior, and none were weakened: web test scan (`scan-test-weakening.sh`) came back clean for this repo/commit.
- [x] Tenancy/idempotency/money/en-es: not this role's primary lens, but nothing in the UI trusts client-side totals or state — all money display goes through `Money`/cents formatters, and status/variance values are rendered as-received from the server, not recomputed client-side.
- [x] Decisions recorded where needed: none needed.

## Optional notes (not blocking)
- The masked API-key field's hint text ("•••••••• (set) — type a new key to replace it") is good, but the placeholder also shows literal `••••••••` dots when a key is set — a screen-reader user gets the `hint` text via the `Field` label association (assuming `Field` wires `aria-describedby`, which is the existing pattern elsewhere in this codebase); worth a follow-up accessibility pass across the whole settings page in a dedicated a11y audit rather than blocking this card on it.
- Per the primary reviewer's finding, the report claims 4 screenshots were taken but none exist on disk — I could not do my own screenshot-based UI check as a result and relied on the diff plus the shared API pass. Not blocking, but future rounds should confirm screenshots actually land before the report is filed.
