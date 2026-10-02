# Wave 7 — multi-channel shops and correct money

**Dates:** 2026-09-26. **Gated:** together with wave 6, as "wave 6+7." **Pushed:** not
immediately — the gate found two real bugs and asked for both to be fixed first.

## What was built
- **T-7-1** Tracking export files for CSV channels (integrations-engineer + web-engineer):
  an Etsy-first shop can upload tracking back to Etsy, Amazon, TikTok and Walmart with one
  file, through a new `exportedAt` timestamp separate from the live-push path.
- **T-7-2** Fees and refunds in profit (backend-engineer/finance + integrations-engineer):
  profit counts real channel fees and refunds, attributed to the *refund's* date through a
  new `refund_events` ledger table, not folded back into the order's own period.
- **T-7-3** Label fee from the plan (backend-engineer/billing, shipping): each plan's label
  fee (for example, $0.10 on the paid plan) is actually charged, not hardcoded.
- **T-7-4** Orders: ship-by holidays, staleness, per-line cancel (backend-engineer/orders):
  ship-by dates respect postal holidays, a re-import can't overwrite a newer local change
  with a stale channel value, and a single line item can be cancelled without touching the
  rest of the order.
- **T-7-5** Accessibility and i18n sweep (web-engineer): keyboard and screen-reader
  support, no English leaking into Spanish screens.

## Why
This wave turns "the office can place orders" into "the numbers the office sees are
actually right." Fees, refunds and label costs all eat into a shop's real margin — if
profit doesn't count them, the owner is making decisions on a fictional number. The
ship-by/staleness fix matters because a channel re-sending an order shouldn't silently
undo a change staff already made locally.

## What went wrong
- The combined wave 6+7 gate (`waves/7/gate.md`) passed every automated check (contracts
  31/31, ui 24/24, imaging green, backend 591/591, web 76/76, floor 86/86, migration 24,
  floor suite 3/3) and all eight smoke checks, but explicitly recommended **"do not push
  yet"** because the full API/browser golden path hit two real bugs:
  - **Bug #1**, a wave-6 regression: the vendor portal inbox always returned 500, traced
    to one exact line in `modules/vendors/service.ts` — a hardcoded `SheetState` list that
    was missing `"printing"`.
  - **Bug #2**, wave 8's own in-flight work: Etsy AI listing drafts could never generate
    without a production partner set, also traced to one exact line.
- The plan review for this wave uncovered a chain of file-ownership gaps before the cards
  even started: T-7-2's card needed `db/schema/finance.ts` and parts of `invai-contracts`
  that weren't in its owned paths; T-7-4 needed a new contract field
  (`NormalizedOrder.sourceUpdatedAt`) that every channel adapter has to populate, which
  crosses into T-7-1's integrations territory. Several explicit grants were made before
  building started to close these gaps, rather than leaving cards to collide mid-build.
- `team/lessons.md` also records a second `git stash`-in-a-shared-tree mistake from this
  wave, even though the rule had already been written down after wave 4 — the rule was in
  the team's shared brief but not repeated in this builder's own prompt.

## What the team learned
- A gate can find small, precisely-located, 100%-reproducible bugs that still block a
  push even when every automated suite is green — "every test passes" and "the real
  golden path works" are different claims, and the gate checks both.
- Written-down rules that live only in a shared brief don't reliably reach every builder;
  from this wave on, prompts repeat the specific "never stash in a shared tree" rule
  directly, not just by reference.
- Money-shape decisions (which period a refund belongs to, whether a label fee is a
  hardcoded constant or reads the plan) are exactly the kind of thing a plan review should
  catch *before* building — several of this wave's clarifications were about getting the
  data model right, not fixing it after the fact.

## Files to look at
- `invai-backend/src/modules/vendors/service.ts` — bug #1's exact `SheetState` list.
- `invai-backend/src/db/schema/finance.ts` — the new `refund_events` table (T-7-2).
- `invai-backend/src/modules/shipping/service.ts` — export timestamp and label fee (T-7-1, T-7-3).
- `invai-backend/src/modules/orders/import.ts` — staleness and per-line cancel (T-7-4).
- `invai-docs/waves/7/gate.md` — both bugs, with their exact file and line.
- `invai-docs/team/lessons.md` (2026-09-26, "Wave 7 stubs" and "Wave 8" `git stash` rows).
