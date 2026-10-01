# Review of T-P5-5 (round 2)

- Reviewer: reviewer on claude-opus-5.5 · Author: web-engineer on claude-opus-5.5
- Verdict: approve

## Evidence I re-ran (own worktree `/tmp/p5-rev-t5r2` at invai-web 0ad173d, node_modules symlinked, removed after)
| Command | Result |
|---|---|
| `tsc --noEmit` / `biome check .` / `vitest run --reporter=dot` (direct binaries; `pnpm` scripts try to install into the symlinked node_modules) | exit 0 / 1 old warning (unchanged from r1) / 23 files, 158 passed |
| `index.tsx` reverted to `0ad173d~1`, `-index.test.ts` at 0ad173d | 1 of 12 failed (AssertionError on the vendorless en line) -> the new test is red without the fix |
| Key sync: `vendor_email_{failed,unconfirmed}_unknown` in `en.ts`, `es.ts`, `scripts/i18n-es.json` | 2/2/2; es.ts == json text; `i18n-es-missing.json` absent |
| `scan-test-weakening.sh invai-web 0ad173d~1` | no hits |
| Backend source `invai-backend/src/modules/vendors/delivery.ts:242` | omits only `vendorName`; `sheetName` always sent, so the fallback `?? ""` on sheetName is unreachable |

## Finding 1 (r1): closed
`index.tsx:522-548` branches on `p.vendorName`; absent -> `*_unknown` key ("the email to the vendor" / "el correo al proveedor"). Test (`-index.test.ts:~170-206`) uses real i18next en+es catalogs, asserts exact text in both languages for both codes and no double space / "to  was" / "a  se".

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | r1 evidence stands; missing-vendorName case now handled |
| 2 | Yes | unchanged since r1 |
| 3 | Yes | es vendorless lines read naturally, no raw key, no English (test above) |
| 4 | Yes | new test red on reverted fix; catalogs in sync |

## Checks
- [x] Only owned paths (5 files: `routes/_app/index.tsx`, `-index.test.ts`, en/es, `i18n-es.json`) · [x] no scope creep · [x] no weakened tests
- [x] Tenancy/idempotency/money n/a (client rendering) · [x] en+es shipped together
- Processes: none started; worktree removed; shared dev DB and gate ports untouched.
