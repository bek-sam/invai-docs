# Review: T-21-4 (help center en/es, runbook) — round 1

Reviewer: product-designer, Sonnet 5. Author: docs-writer.

## Verdict: approve

## Context
An earlier product-designer review pass caught an untranslated English word "transfers" in
`help/es/receiving.md` and its `help/es/index.md` reference, but stopped before writing a verdict
file. docs-writer fixed it in commit `4e6eb24` ("Fix untranslated \"transfers\" in help/es
(receiving.md, index.md, and 2 more misses)"), which also swept the rest of `help/es/**` and found
4 more genuine misses in `gang-sheets-and-vendors.md` (x3) and `profit-and-ad-spend.md` (x1). This
review re-verifies that fix and does a fresh spot-check.

## Evidence
- `git -C invai-docs show 4e6eb24` — diff replaces every stray "transfers" with "transferencias"
  in `receiving.md` (title, H1, 2 body sentences, gender agreement "listos"→"listas"),
  `index.md`, `gang-sheets-and-vendors.md` (x3, matching gender agreement), and
  `profit-and-ad-spend.md` (x1). `waves/21/reports/T-21-4.md` "Round 2" section documents the fix
  against `invai-floor/src/i18n/es.ts` (`tabSheets: "Transferencias del proveedor"`).
- `grep -rniE '\btransfers?\b' invai-docs/help/es/` → no hits (clean).
- `grep -rniE '\b(tenant|company_id|RLS|queue|outbox|webhook|payload|mock|procedure)\b' invai-docs/help/es/` → no hits.
- Spot-checked 3 Spanish articles against `.claude/skills/write-plain-language-copy/glossary.md`:
  `receiving.md` and `gang-sheets-and-vendors.md` (the two fixed files) and `sku-mapping.md` (not
  touched by the fix, as a control). All use correct glossary terms: prenda, transferencia, hoja,
  proveedor, estación, plancha, envío, SKU. "Gang sheet" correctly kept in English per glossary.
- `ls invai-docs/help/en invai-docs/help/es` → both list the same 14 slugs
  (`ai-listings-and-trademark-check`, `csv-tracking-export`, `floor-tablet-setup`,
  `gang-sheets-and-vendors`, `getting-started`, `index`, `plans-and-billing`,
  `profit-and-ad-spend`, `receiving`, `shipping-labels-and-tracking`, `sku-mapping`,
  `team-and-roles`, `the-assistant`, `weekly-digest`) — matched.

## Blocking findings
None.

## Optional notes
None.
