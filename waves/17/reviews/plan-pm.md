# Wave 17 plan review — product-manager

**Verdict: approve**

## Scope fit (scope.md item 13, "AI business assistant (read-only tools)")
- T-17-1 (contract enum), T-17-2 (4 new tools), T-17-3 (loop/prompt v4) and T-17-4 (chips/starter questions) all stay inside item 13: every new tool is read-only, runs under `withTenant`, changes nothing, and the assistant is the existing AI-assistant surface, not a new one. Fits.
- The spec correctly draws the line at two ideas and puts them out of scope instead of building them: external market signals and a scheduled digest. Both are a different shape than "read-only tools called by the owner" (one needs an outside data source and carries marketplace-ToS risk; the other is a pushed, unattended surface with new recurring AI spend). Filed as SCR-001 and SCR-002 below — correctly not built.
- No pricing, plan-limit or new-integration scope creep in any card.

## Spec quality (`specs/assistant-business-analyst.md`)
- Evidence: grounded in a real gap analysis of the shipped assistant (6 tools, no comparisons, no ad efficiency, no fulfillment health) rather than a one-shop quirk. Acceptable for a wave that improves an existing MVP-in feature; no pilot is live yet to cite a ticket.
- Acceptance criteria: tightened all 10 into explicit Given/When/Then. Added two edge cases the draft didn't test for testability: AC9 (small shop, single channel, no ad spend — tools must return nulls/empty lists, not errors) and AC10 (a disconnected/errored channel — must be excluded and flagged `incomplete`, not silently presented as complete). Both are consistent with behavior the tool table and honesty rules already implied (ROAS null at zero spend, `incomplete` flags), so this is tightening, not new scope.
- Segments: added a short section — mid is the primary target (matches the demo-seed criteria), small must degrade gracefully (AC9), large is covered by existing row caps and the bounded 10-iteration loop with no large-specific behavior needed this wave.
- Added Success metrics (adoption of the new tools, qualitative trust signal) and Open questions sections, since these were missing; marked metrics as directional pending the data-analyst's `define-metric` once a pilot is live (role is dormant pre-pilot, correctly).
- Status changed from "draft, PM to confirm" to confirmed.
- I did not touch `wave.md` or the T-17-* cards (tech lead's files).

## Cards vs. spec
- T-17-2's acceptance criteria already cover ROAS-null-at-zero-spend (AC3) and channel-scoped cross-listing gaps (AC4) — consistent with the spec's new AC9. Recommend the tech lead add one line to T-17-2 confirming `get_ad_performance`/`get_design_insights` are exercised with a single-channel, no-ad-spend fixture (not just the two-company tenancy fixture), so AC9 has a concrete test home. Not blocking; flagging for the tech lead.
- T-17-3's shop-context block (time zone, channels, currency) gives the assistant what it needs to say "data may be partial" per AC10 when a channel is disconnected — no gap found.

## Scope-change requests filed
- `product/scope-changes/SCR-001-assistant-external-market-signals.md` — recommend defer; sent to owner as **OI-6** (spend + marketplace-ToS/scraping risk to pending Etsy/Amazon approvals).
- `product/scope-changes/SCR-002-assistant-weekly-digest.md` — recommend defer; sent to owner as **OI-7** (new recurring AI spend + unattended outbound surface, beyond item 13's "read-only tools" shape).

## Backlog
- Added `B-113` to `waves/backlog.md`, status `planned (wave 17)`.
