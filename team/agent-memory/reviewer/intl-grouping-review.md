---
name: intl-grouping-review
description: Intl.NumberFormat grouping facts (Node 24/TS 7) for reviewing money/number formatter cards — useGrouping "always" vs minimumGroupingDigits
metadata:
  type: reference
---
2026-10-01 T-P3-3: `minimumGroupingDigits` is NOT an ECMA-402 option (ICU-only); Node 24 ignores it. The standard equivalent is `useGrouping: "always"` (or `true`), typed in TS 7 `lib.es2023.intl.d.ts`, fixes bare `es` 4-digit amounts (`1.234,56 US$`) and leaves en unchanged.
**How to apply:** when a card hand-rolls digit re-grouping, diff it against `useGrouping:"always"` across many locales/currencies/amounts with a /tmp node script (0 diffs = correct). The guard hook blocks `$'\x..'` in bash; count NBSP bytes with python3 instead.
