---
name: i18n-false-positives
description: Two things that look like screen-check bugs but aren't — check before filing
metadata:
  type: project
---

A repeated generic buyer name in the orders list/drawer ("Buyer") is not a bug: on aged seed
history the field is literally `buyerName: "Buyer (data purged)"` (the PII-purge feature working
as intended), and the web's `firstName()` (`invai-web/src/lib/format.ts`) correctly takes the
first word. Confirmed by calling `orders.list` as owner directly (oRPC client, cookie session) —
cheaper than guessing from the screenshot alone.

An English loanword left untranslated in `es.ts` isn't automatically a new bug: check
`invai-docs/team/skills/write-plain-language-copy/glossary.md` first. "Transfer(s)" is a
documented, already-tracked inconsistency (floor says "Transferencia", web says "Transfer") —
don't re-file it.

Before filing a "date/heading shows English in Spanish UI" bug, grep for `dateLocale(` in
`invai-web/src/lib/format.ts` and check whether the offending call goes through it — B-207 was
exactly this bug, already fixed there with a documented helper; a new instance is a straggler
that skipped the helper, worth citing precisely rather than filing as a fresh unknown bug.

Related: [[floor-screen-check]]
