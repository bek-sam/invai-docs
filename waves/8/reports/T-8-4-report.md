# T-8-4 report: Trademark-risk gate (B-46)

**Status:** done, ready for review (co-reviewers: compliance-officer, product-designer; flags:
marketplace-policy, ui).
**Commits:** backend `f3b0eea`, web `98a47a9` (both pushed to `origin main` per the standing
push-directly-to-main rule; no new contracts/migration work needed — the architect's `4f4efcd`/
`e958638` already shipped the full stub).

## What changed

**`invai-backend/src/modules/ai/trademark.ts`**
- New `assertTrademarkGate(tm, reviewed)`: `riskLevel === "high"` always throws
  `HIGH_TRADEMARK_RISK` (no override, no parameter to bypass it). `riskLevel === "medium"` throws
  `TRADEMARK_REVIEW_REQUIRED` unless `reviewed` is true. `low`/`null` passes. One function, called
  identically from all three enforcement points so the three ranges can't drift out of sync.

**`invai-backend/src/modules/ai/service.ts`**
- `approveDraft`: dropped the `acknowledgeRisk` parameter and the old "high risk unless
  acknowledged" check entirely; calls `assertTrademarkGate(row.trademark, !!row.trademarkReviewedBy)`
  instead. Always reads the row it just loaded in this call (`loadDraft` with `for update`), so
  it's the current trademark field, never a value cached earlier.
- `publishDraft` and `exportListingsCsv` had **no trademark gate at all** before this card (a
  draft could be approved under the old rules, edited in a way that changed nothing gate-visible,
  then published/exported unchecked). Both now call the same `assertTrademarkGate` against the
  row they load fresh in that call, before touching connections/CSV/S3.
- New `recordTrademarkReview(tx, ctx, id, note)` (`ai.listings.recordTrademarkReview`): 409
  `TRADEMARK_REVIEW_NOT_APPLICABLE` unless the draft's current `trademark.riskLevel === "medium"`
  (including when `trademark` is null); otherwise sets `trademarkReviewedBy/At/Note` and
  audit-logs `listing_draft.trademark_review` with `{riskScore, note}`, exactly per wave.md.

**`invai-backend/src/modules/ai/router.ts`**
- Wired `recordTrademarkReview` (was a `NOT_IMPLEMENTED` stub). `approve`'s handler no longer
  forwards the contract's deprecated `acknowledgeRisk` input flag to the service.

**`invai-backend/src/modules/ai/service.test.ts`** (shared file; only my hunks — the trademark
gate/range coverage)
- Updated the existing approve-gate assertions: a title with a trademarked phrase now stays
  blocked on every attempt (no bypass), and only clears once the text itself is edited away.
- New `describe("trademark gate (T-8-4, ...)")`: for each of the three ranges I force the draft's
  `trademark` field directly (via `withSystem`) to an exact score/level so the *gate* is under
  test independent of the trigram scoring (already covered by the "trademark scoring" describe).
  Cases: `< 25` approves clean; `25-59` blocks with `TRADEMARK_REVIEW_REQUIRED` until
  `recordTrademarkReview` (also checks it 409s on a non-medium draft), then approves; `>= 60`
  blocks even with a review forced directly onto the row (proving there's no override, not even a
  stale one); and a live-recheck case that approves at low risk, then mutates the row's
  `trademark` to high and confirms both `publishDraft` and `exportListingsCsv` block on the
  *current* value rather than what was true at approval.

**`invai-web`**
- `src/routes/_app/listings/drafts.$draftId.tsx`: removed the "Approve anyway" `ConfirmDialog`
  and the `acknowledgeRisk` flag from the approve call. `TRADEMARK_REVIEW_REQUIRED` from either
  `approve` or `publish` now opens a review dialog (min-3-char note) wired to the new
  `recordTrademarkReview` mutation; `HIGH_TRADEMARK_RISK` just shows the server's own message
  (self-explanatory, next to the always-visible trademark panel). Added a prominent banner near
  the top of the page for any flagged listing (`riskScore >= 25`) — high says why it's blocked,
  medium says a review is needed or shows that one's already on file — closing T-8-1's AC4 ("a
  listing that the trademark check flags shows the notice"), which that card explicitly left to
  this one. The trademark panel now also shows the recorded review (who/when/note) once one
  exists.
- `src/components/confirm-dialog.tsx`: added an optional `confirmDisabled` prop (used to keep the
  review dialog's button off until the note has real content).
- `src/i18n/en.ts` / `es.ts`: added strings for the review dialog and the flagged-listing
  notices; removed the now-orphaned `highRisk`/`highRiskHint`/`approveAnyway` strings (grepped
  clean — nothing else referenced them).

## Decisions
- **Gate logic lives once, in `trademark.ts`, not duplicated three times in `service.ts`.** All
  three enforcement points (`approveDraft`, `publishDraft`, `exportListingsCsv`) call the same
  `assertTrademarkGate`, so the two thresholds can't drift between them.
- **`exportListingsCsv` gates per-draft before resolving any product/variant data**, so a bulk
  export request fails fast (before hitting S3 or needing blank-variant rows) if any one draft in
  the batch is currently gated. The list page's existing bulk-export error handling already
  surfaces the server's message verbatim, which is self-explanatory for both codes, so I left
  that call site's error handling as-is rather than building a multi-draft review flow there.
- **`recordTrademarkReview` doesn't check draft status** (only `riskLevel === "medium"`) — a
  compliance review can be recorded on a `needs_review` draft before anyone tries to approve it,
  not only in reaction to the 409. Matches wave.md's contract stub, which has no status
  precondition either.
- **Test DB/Redis/port numbers per the card** (`invai_test_t84`, port 3184, `REDIS_URL` /4);
  dropped/flushed after the runs.

## Verification
- `pnpm typecheck && pnpm lint` clean in `invai-backend` and `invai-web`; `invai-web`'s `pnpm
  build` succeeds (pre-existing >500kB chunk warning, unrelated).
- Backend focused run: `src/ai/ai.test.ts`, `src/modules/ai/service.test.ts`,
  `src/modules/channels/listings.test.ts` — **56/56 passed**, including the new 4-case trademark
  gate describe (< 25 / 25-59 / >= 60 / live re-check at publish+export).
- Backend full `vitest run`: **79 files / 595 tests, all passed** (no repeat of the Shopify
  OAuth-state flakiness T-8-1 saw).
- Real-DB spot check (not just the assertion): queried `audit_log` after the medium-risk test ran
  and confirmed a `listing_draft.trademark_review` row with `data: {riskScore: 40, note: "..."}`,
  matching wave.md's audit shape exactly.
- No live API/browser pass: the card's own unit tests already exercise the real service functions
  against a real Postgres database (not mocked) end to end for every acceptance criterion; given
  the token budget I judged that sufficient over also standing up the dev server/browser for a
  UI click-through. Flagging this as a gap the reviewer may want to close with one browser pass
  on the new review dialog.

## Known gaps and cross-card notes
- **A concurrent edit landed mid-task.** While I was working, another agent committed
  `a32b682` ("Fix: sanitize the assistant chat text ask() stores", T-8-2 r2) directly into the
  same shared `service.ts` I was editing. I caught it via `git diff` before staging, confirmed
  those hunks were unrelated to my card and already committed upstream of my change, and staged
  only my own hunks (`git add <paths>` after inspecting `git diff --cached --stat`) — nothing of
  theirs is in my commit.
- **No new contracts/migration work was needed.** The architect's stubs (`4f4efcd` contracts,
  `e958638` backend, migration `0023`) already had `TrademarkReview`, `recordTrademarkReview`'s
  full shape, both error codes, and the DB columns exactly as wave.md specified; this card only
  implemented the enforcement and the review-recording logic against them.
- **T-8-1's AC4 (trademark notice) is closed by this card's web change** (the banner + panel), as
  wave.md's file ownership intended.
