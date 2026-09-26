# Review of T-8-4 (round 1)

- Reviewer: product-designer on sonnet
- Author: ai-engineer + web-engineer on sonnet
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web diff 5c6ab28 98a47a9 -- src/routes/_app/listings/drafts.\$draftId.tsx src/components/confirm-dialog.tsx src/i18n/en.ts src/i18n/es.ts` | read in full |
| web worktree at `98a47a9`: `tsc --noEmit`, `biome check .`, `vite build` | all clean (see reviewer's file for exact output) |
| `grep -rn "bg-danger\|bg-warning" invai-web/src` and `grep -n "RelativeTime" invai-ui/src/index.ts` | both tokens/exports are real and already used elsewhere in the app — this diff doesn't invent one-off styling |

## Acceptance criteria (design lens)
| # | Met? | Evidence |
|---|---|---|
| Dialog: replaces "approve anyway" with a review-note flow | Yes | The destructive `ConfirmDialog` ("Approve anyway") is gone entirely. The new dialog (`reviewOpen`) opens only on `TRADEMARK_REVIEW_REQUIRED`, is non-destructive (no red confirm button), and requires a real note: `confirmDisabled={reviewNote.trim().length < 3}` mirrors the server's `min(3)` so the button is disabled before a failing request is even attempted, not just caught in an error toast. |
| Dialog: no path to bypass high risk | Yes | `HIGH_TRADEMARK_RISK` opens no dialog — the server's own message is shown as a toast, and the always-visible banner + trademark panel explain why. There is no button anywhere that submits `acknowledgeRisk`. |
| Banner: visible for any flagged listing (>=25), states which range and what's needed | Yes | Three distinct copy states cover high / medium-unreviewed / medium-reviewed, each naming the score. Correct precedence: `riskLevel === "high"` wins over the reviewed check, so a stale review can't make the banner claim "cleared" for a draft that has since become high-risk. |
| Banner and dialog work in en and es | Yes | Diff is 1:1 across `en.ts`/`es.ts`: 6 new keys in each, same 3 keys removed from both (`highRisk`, `highRiskHint`, `approveAnyway`), confirmed nothing else in the codebase still references the removed keys. Spanish copy reads naturally, not a literal machine translation of the English (e.g. "revisado por cumplimiento, listo para publicar" rather than a word-for-word gloss). |
| Recorded review is visible where a reviewer would look for it | Yes | The trademark panel now shows who/when (`RelativeTime`) and the note once `trademarkReview` exists, right under the existing `TrademarkResult`, so the reviewer doesn't have to leave the page or open the dialog again to see what was recorded. |
| Approve/publish buttons stay usable after a review is recorded | Yes | `recordReview`'s `onSuccess` closes the dialog and invalidates the query; the user re-clicks Approve/Publish themselves. This is a deliberate (and reasonable) choice — auto-retrying a mutation the user didn't explicitly re-trigger would be a surprising side effect — but it does mean one extra click; noted below, not blocking. |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope — `confirm-dialog.tsx`'s new `confirmDisabled` prop is additive and optional, doesn't change any other caller's behavior (default `undefined` -> `disabled={pending || undefined}` behaves as before)
- [x] en/es parity checked key-by-key, not just file-length
- [x] No new colors/classes invented; reuses existing `bg-danger`/`bg-warning` tokens and `AlertTriangle` icon already in use elsewhere on this same page

## Optional notes (not blocking)
- After recording a review, the user must click Approve/Publish again themselves — a small UX nicety would be auto-resubmitting the original action on review success, but the current behavior is safe and not confusing (the dialog closes, the banner updates to the "reviewed, cleared to publish" state, and the button is right there).
- I did not drive a real browser for this round (see the reviewer's note on token budget); I verified the dialog/banner logic by reading the diff plus a clean `tsc`/`build`. A one-pass browser screenshot of the medium-risk flow (banner -> dialog -> recorded state) would be a good, cheap follow-up rather than a blocker here.
