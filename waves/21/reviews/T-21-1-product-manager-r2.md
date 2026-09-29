# Review: T-21-1 Legal drafts for counsel — product-manager (domain), round 2

Reviewer: product-manager  Verdict: **approve**

## Fix 1: `legal/dpa.md` §8 English sentence

Read the new text: "export, then delete it within 30 days of a deletion request (no separate export-only
window is offered; the export and the deletion clock run together)." This parses cleanly and now matches
the meaning already present in `legal/es/dpa.md` lines 108–109 ("no se ofrece un plazo de solo-exportación
por separado; la exportación y el plazo de eliminación corren juntos"), which r1 confirmed was the correct
intended fact. No new claim introduced, no evidence citation changed (`service.ts:283,372,581,653` line
unaffected by the diff). Fixed.

## Fix 2: OI-19 deadline

`owner-inbox.md` now reads "Deadline: 2026-10-12 17:00 America/Phoenix", matching the
`escalate-to-owner` template's `YYYY-MM-DD HH:MM TZ` format. This was a nit in r1, not a blocker, but it's
correctly resolved and doesn't conflict with the "Cost of waiting" text, which still says nothing in waves
21–22 depends on it.

## Scope of round 2

Diff is exactly the two lines identified in r1 (`legal/dpa.md`, `owner-inbox.md`), nothing else touched —
confirmed via `git show 30b1506 --stat`. No re-check needed on scope, Spanish completeness, placeholders,
plain-language claims or the fact-citation table; r1 already verified those against the code and they are
unaffected by this diff.

## Verdict

**approve**. All 5 acceptance criteria met, the one requested fix is correct and grammatical, and the OI-19
nit is resolved. No further rounds needed from product-manager.
