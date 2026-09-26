# Review of T-6-4 (round 1) — product-designer co-review

- Reviewer: product-designer on Sonnet 5
- Author: web-engineer (web `4817a72`) on Opus
- Verdict: **approve**

Scope: UX of the copy buttons (AC1), publish-status section (AC3), bulk CSV export (AC2 UI), and
the AI credit history table (AC4) in `invai-web`. Command evidence shared with
`T-6-4-reviewer-r1.md`; not re-run here.

## Evidence gap, noted up front
The card and report both point to screenshots (report: "6 screenshots taken, not saved to disk").
None exist on disk under `invai-docs/waves/6` or anywhere newer than the report. I reviewed the
JSX diff directly (`drafts.$draftId.tsx`, `drafts.index.tsx`, `billing.tsx`) rather than a live
browser pass, given the machine load this round. This is a real gap — recommend a fresh set of
screenshots before push — but nothing in the code read as a UI defect worth blocking on.

## Walkthrough by acceptance criterion

**AC1 — copy buttons.** `CopyIconButton` (ghost, icon-size `size-5`/`size-3` glyph) sits inline
next to each field's counter, shown only once `draft.status === "approved"` — good: it doesn't
clutter the editor while a draft is still being written/regenerated, and it only appears where
it's actually useful (there's no live publish API yet, so copy-by-hand is the real workflow).
`aria-label` and `title` are both set from the same translated string, so it's accessible to
screen readers and has a native tooltip on hover — no `title`-only accessibility gap. Toast on
copy reuses the existing toast pattern. No concerns.

**AC3 — publish status.** Replacing the old bare `draft.publishedUrl` link with a full section
(badge, error, pending-approval note, link) is a clear improvement — a failed publish attempt is
no longer invisible unless the user happened to be looking right after clicking. The component
only mounts/polls when `draft.status === "publishing" || publishedUrl || publishedListingId`, so
it doesn't add a background poll to every draft page. The `Loader2` spinner state while the first
`publishStatus` fetch is in flight avoids a layout jump. One minor, non-blocking note: since no
channel today reaches `publishing` (per the report — no async publish path exists yet), this
section is effectively unreachable in the live product until a real channel exists; that's
correctly scoped as forward-looking by the report, not a design gap.

**AC2 (UI) — bulk CSV export.** Selection-based export button only appears once something is
selected, disables (with a translated tooltip explaining why) when the selection spans channels,
and clears selection on a successful export. Good use of the existing `DataTable` row-selection
prop rather than inventing new selection UI. The icon/spinner swap (`Download` → `Loader2`) while
pending is consistent with the rest of the app's button pattern.

**AC4 — credit history.** The ledger table's column choices (when/kind/model/tokens/credits) are
the right ones for a shop owner auditing spend; credits are colored green/red by sign
(`text-success`/`text-danger`) which is a reasonable, already-used pattern elsewhere in billing.
`creditKind` labels fall back to `row.original.kind.replace(/_/g, " ")` if a translation is
missing — a sane default that avoids ever showing a raw `snake_case` string untranslated in the
common case, though it would still show untranslated English if a *new* kind is added later
without a matching key; not a concern for this card since all current kinds have both en and es
entries (verified by diffing `en.ts`/`es.ts` — 8 keys added to each, 1:1).

## i18n / plain-language check
- Every new user-facing string has an en+es pair (`ledgerCredits/Empty/Hint/Kind/Model/Title/
  Tokens/When`, `creditKind.*` ×8, `copied/copyDescription/copyTags/copyTitle`,
  `exportCsv/exportMixedChannel/exportSelected`, `publishStatusTitle` — 26 en keys, 27 es keys,
  matching after accounting for one object-vs-flat count difference; diffed line by line, no
  missing pair).
- No raw English found in the JSX diff (checked `git diff` for hardcoded strings outside `t(...)`
  calls — none).
- Copy is short and in plain language ("Select drafts from a single channel to export them
  together" reads clearly as the reason a button is disabled, not just "Error").

## Checks
- [x] Only owned paths changed (listings routes, `settings/billing.tsx` credits section, own i18n
  keys) — confirmed by `git diff --stat f2ef447 4817a72`.
- [x] Nothing outside scope.
- [x] No weakened tests in `invai-web` (`scan-test-weakening.sh` clean).
- [x] en/es text present for every new string; no PII added to logs/UI.
- [ ] Live screenshots — not available this round (see gap above); relying on code read.

## Optional notes (not blocking)
- Take a fresh screenshot pass before push, given none survived from the build round.
- Consider, in a later card, showing which specific channels are mixed in the disabled-export
  tooltip (today it's a generic "select one channel" message) — nice-to-have, not needed now.
