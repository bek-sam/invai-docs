# Review of T-26-5 (round 2)

- Reviewer: product-designer on Opus 5.5
- Author: web-engineer (commit co-authored "Claude Opus 5.5")
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web show --stat c471c95` | 5 files, matches card's owned paths |
| Read `invai-web/src/routes/_app/listing-photos.tsx:604-623` | credits-short reason now a visible `<p>` sibling of the Generate button, not a `title` tooltip |
| `grep -n "grid-cols" invai-web/src/routes/_app/listing-photos.tsx` | lines 193, 764: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4` on both grids |
| Read `/tmp/t265r2/01-pickdesign-390-es-light.png` | pick-design grid renders one column at 390 px, es, light |
| `cd invai-web && pnpm typecheck` | pass, 0 errors |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 4 generate disabled with the reason | yes | visible text (no longer tooltip-only), see code above |
| 9 usable at 390 px, grid becomes one column | yes | both grids fixed; shot 01 confirms pick-design grid at 390 px; results grid uses the identical class, same fix |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`git diff --stat` matches card's owned globs)
- [x] Nothing outside scope
- [ ] n/a — test suite / weakening scan is primary reviewer's scope
- [x] en/es text present (credits-short string already existed; no new strings needed for this fix)
- [ ] n/a — tenancy/idempotency/money not in my review scope

## Optional notes (not blocking)
- Results grid (line 764) at 390 px was not independently screenshotted this round, only the pick-design grid (shot 01); it uses the identical Tailwind classes so the fix applies equally, and the r1 finding already confirmed both grids shared the same bug.
