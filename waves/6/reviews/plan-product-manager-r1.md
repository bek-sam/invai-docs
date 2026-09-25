# Product-manager review of the Wave 6 plan (round 1)

- Reviewer: product-manager
- Author: tech-lead
- Verdict: **approve with clarifications** — applied to `wave.md` and all 5 cards; no scope change needed, one scope *question* raised for the owner/PM to decide (below).

## What I checked
`agent-brief.md`, `scope.md`, `wave.md`, each `T-6-*.md` card, and `build/audit-2026-09-24.md`'s B-86/B-87/B-88/B-89/B-101 entries — against: does each card trace to `scope.md` or the always-in-scope carve-out, are the acceptance criteria testable and user-meaningful, do the web paths actually not collide, and is anything smuggled in outside scope. I also read the code the cards name (contracts, the relevant backend modules, the web routes) read-only, per this review's instructions — no DB, no server, no commit to `invai-contracts`.

## Scope traceability
| Card | Ref | Traces? |
|---|---|---|
| T-6-1 | `scope.md#mvp-in` item 6 (blank inventory, POs, receiving) + B-86 | Yes. Manual PO entry, mark-placed-manually and receive idempotency are squarely "POs, receiving." |
| T-6-2 | items 4 (production floor app) and 5 (blank inventory) + B-87 | Yes. In-house printing and reprints are production-floor (item 4); bins-holding-blanks and blank labels are inventory (item 5). |
| T-6-3 | item 8 (profit per order, design, blank, channel) + B-88 | Yes. Ad spend, allocation and export/drill-down are all "profit," not new functionality. |
| T-6-4 | item 10 (AI listing drafts) + B-89, B-101 | Yes. Copy/export/publish-status/credits are the shipped feature's finishing edges, and B-101 is a straightforward always-in-scope bug/security fix (a dead branch that `JSON.parse`s encrypted credentials, a placeholder SKU shipped to real marketplaces, credits not charged on disconnect). |
| T-6-5 | always-in-scope: security and money (B-109) | Yes, and it's the sharpest of the five — a sample workspace that can spend real money or send real mail is a trust incident, not a feature gap. |

Nothing here is new functionality outside the MVP-in list; nothing from the "MVP: out" list (direct Amazon/Etsy/TikTok/Walmart APIs, AI design generation, etc.) sneaks in — T-6-4's `exportCsv` explicitly stays on the CSV path for channels without API access, which is the correct MVP-out boundary.

**One scope question, not blocking:** while checking every real-provider adapter for T-6-5 (see the architect review), I found blank-supplier ordering (`integrations/suppliers/index.ts`, live when a company has its own S&S credentials) has no demo guard and isn't mentioned in T-6-5's acceptance criteria at all. It's the same class of risk as the carrier/marketplace guards this card exists to add. I did not fold it into T-6-5 unilaterally — that's a scope decision, not a plan-clarity one — but the owner should decide via `scope-change-request` whether it's in this wave or deferred, rather than it silently falling through the cracks because no card names it.

## Acceptance criteria: testable and user-meaningful
Mostly solid — concrete, checkable outcomes (a state transition, a CSV row, a masked field, a mock-vs-live spy assertion) rather than vague goals. Two were not testable as written, now fixed on the cards:
- **T-6-1 AC3's "a PO stuck in `submitting` for more than 15 minutes raises an alert"** had no verification method that fits inside a token-budgeted browser pass — nobody should sit through a real 15-minute wait. Added: test it with a backdated `submittedAt` fixture instead.
- **T-6-2 AC2's "count by reason and by week"** had no backend endpoint to draw from — `production.reprints.stats` only returns one flat total for a period, no per-week series. This wasn't a testability problem so much as the AC describing a UI for data that doesn't exist yet; the architect review adds the missing `reprints.reasonsByWeek` stub, and I've pointed the card at it.

Everything else reads fine as-is: T-6-1's manual-PO/mark-placed/receive/count/settings ACs are all concrete UI+backend behaviors a real office user would notice; T-6-3's ad-spend/profit/export/drill-down ACs map directly to "can I see what I actually made"; T-6-4's copy/export/publish-status/credits ACs map to "can I actually use these drafts"; T-6-5's ACs are about as testable as a security card gets (spy/fetch-mock assertions, a regression test pinning the column check).

## Web path overlaps
Checked file-by-file against the "Web file ownership" table: `routes/_app/inventory/**`+`features/inventory/**` (T-6-1), `routes/_app/production/**`+`features/production/**` (T-6-2), `routes/_app/analytics/**`+`settings/costs.tsx`+`features/finance/**` (T-6-3), and `routes/_app/listings/**`+`features/listings/**`+the credits section of `settings/billing.tsx` (T-6-4) don't touch the same file — confirmed no glob overlap and no shared route file between any two cards.

That said, "no file overlap" isn't the same as "no cross-card dependency," and I found real ones (detailed in the architect review, applied to the cards):
- T-6-2's bin/blank labels call T-6-1's `inventory.blankLabels` — a real build-order dependency between two cards both scheduled to start together.
- T-6-2's in-house printing needs a `printsInHouse` company setting whose natural home (`invai-contracts`'s tenancy schema, `modules/tenancy/service.ts`) is T-6-5's territory this wave, not T-6-2's owned paths. Flagged as needing a grant, same pattern as wave 5's checklist-ownership finding.
- Adding the `printing` state to `SheetState` breaks `invai-web/src/components/badges.tsx` (`SHEET_TONE: Record<SheetState, Tone>`), a shared component outside T-6-2's glob.

None of these are scope problems — they're ownership/sequencing gaps the architect review resolves with grants and an explicit checkpoint, now written into `wave.md` and the affected cards.

## In-house print state design, label rendering, exportCsv format, T-6-5's guard coverage
Deferred to the architect review for the technical substance (contract shapes, which files, which library) — I read enough of the same evidence to agree with its conclusions: the `printing` state addition is architecturally sound and additive, imaging (not a backend PDF) is the right place for QR label rendering (Node has no QR library; imaging already renders sheet QR codes), `ai.listings.exportCsv` genuinely has no Shopify branch today, and T-6-5's owned paths as written would leave real gaps (AI-publish, availability checks, sync jobs, and every carrier call site) uncovered even after AC1's column fix. From a product/scope lens, none of these findings expand what's being built beyond what the cards already promise — they make the cards actually deliver what they promise.

## Changes applied
`wave.md` gained the "Contract stubs (exact)" section (7 stubs) and a "Clarifications from the plan review" note. All 5 `T-6-*.md` cards got targeted AC/owned-paths edits per the findings above. No `invai-contracts` commit made. One scope question (blank-supplier demo guard) left open for the owner/PM, not resolved unilaterally here.
