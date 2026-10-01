# Review of T-P3-3 (round 1)

- Reviewer: reviewer on Claude Opus 5.5
- Author: product-designer on Claude Opus 5.5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `invai-ui`: `pnpm typecheck && pnpm lint && pnpm test` | typecheck ok; biome 54 files ok; 5 files / 30 tests passed |
| New `money.test.ts` run on base `0649165~1` (git archive in /tmp) | 3 failed / 9 passed: the es 4-digit, negative and cache tests fail on the old code, as they should |
| `scan-test-weakening.sh invai-ui 0649165~1` | no hits |
| Node 24.21: `minimumGroupingDigits:1` on `es` | ignored (not in `resolvedOptions`, still `1234,56 US$`). Author's claim holds |
| Node 24.21: `useGrouping:"always"` (and `true`) on `es` | `1.234,56 US$`, `-1.234,56 US$`; en stays `$1,234.56` |
| Probe /tmp/p3probe.mjs: the author's re-grouping vs `useGrouping:"always"` for 18 locales (es, en, es-US/MX, pl, pt, fr, de, de-CH, en-IN, hi, ar-EG, ja, it, ca, bg, hu, ro) x 5 currencies (USD EUR JPY MXN BHD) x 17 amounts (0, ±5, ±123,45, ±1.234,56, 1.000,00, 7-, 9- and 12-digit) | 0 differences; en output identical to the old formatter in every case |
| `invai-floor` / `invai-web` `pnpm typecheck` | both pass (builds not re-run) |
| grep web/floor src+e2e for pinned ungrouped es amounts (`dddd,dd US$`) | none, so no consumer test breaks |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | es `1.234,56 US$`, en unchanged (probe above). Not done through `minimumGroupingDigits`, which does nothing at runtime |
| 2 | Partly | es 3-, 4-, 7-digit and negative 4-digit are pinned. en is pinned only for 4 digits (new) and 7 digits (an older test, default locale). There is no en 3-digit and no en negative 4-digit test |
| 3 | Yes | key is still `${locale}:${currency}` (`money.tsx:27`); the test checks USD/es, EUR/es and USD/en in one run |

## Blocking findings
1. `invai-ui/src/app/money.test.ts:29-53`: AC2 is not fully met. There is no en 3-digit test and no en negative 4-digit test. The change sends every locale's negative amounts through the new `formatToParts` and join path (`money.tsx:69-75`). A future edit that breaks the en minus sign (for example a regex on the integer part) would pass this suite. Fix: add `formatMoney(12345,"USD","en")` → `$123.45` and `formatMoney(-123456,"USD","en")` → `-$1,234.56`, with the locale passed explicitly.

## Checks
- [x] Only owned paths changed (`money.tsx`, `money.test.ts`; working tree clean)
- [x] Nothing outside scope
- [x] Tests exercise the behavior and fail on base; nothing weakened
- [x] Tenancy/idempotency n/a; money still integer cents; no new strings
- [x] Decisions: the reason for not using `minimumGroupingDigits` is in the report and in the code comment

## Optional notes (not blocking)
- The standard ECMA-402 option `useGrouping: "always"` is the real equivalent of `minimumGroupingDigits: 1`. It is typed in TS 7's `lib.es2023.intl.d.ts` (the repo's lib is ES2023) and works in Node 24, Chrome 106+, Safari 15.4+ and Firefox 116+. It gives byte-identical output to the 40 hand-written lines (0 differences above), and it avoids running `formatToParts` and allocating an array on every `Money` cell. Consider switching to it in r2. If you keep the custom code, the comment at `money.tsx:59-63` should not say Intl has no native way to do this.
- Consumers: web and floor depend on `"@invai/ui": "link:../invai-ui"`, and its exports point at `./src/index.ts`. Both apps compile invai-ui's source straight from the sibling checkout. invai-ui is its own git repo, so the gate must push invai-ui and run the web and floor builds against it.
- Pre-existing, not this card: `formatMoney` divides by 100 for zero-decimal currencies (JPY 123456 → `1.235 JPY`).
