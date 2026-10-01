# Review of T-P7-2 (round 1)

- Reviewer: reviewer on claude-opus-5-5
- Author: product-designer on claude-sonnet-5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `invai-ui`: `pnpm typecheck && pnpm lint && pnpm test --reporter=dot` | exit 0; 6 files, 35/35 tests (one pre-existing `NO_I18NEXT_INSTANCE` stderr from `pin-pad.test.tsx`, not this card) |
| `invai-web`: `pnpm typecheck && pnpm lint && pnpm test && VITE_API_URL=http://localhost:3000 pnpm build` (consumer, at f20021b) | exit 0; 24 files, 163/163; built |
| New test against base (`git archive 52af2b8~1` + copied `confidence-badge.test.tsx`) | FAILS (`./confidence-badge` does not resolve), as expected |
| `scan-test-weakening.sh invai-ui 52af2b8~1` | no hits |
| python: kit `confidenceBand.*` en/es vs web `market.band.*` at `f20021b~1` | identical in both languages |
| `grep ConfidenceBadge invai-ui/src/index.ts` | export line present (`src/index.ts:11`) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `confidence-badge.tsx:14-24` exhaustive `Record<ConfidenceBand, …>`: high success/ShieldCheck, medium warning/FlaskConical, low outline/CircleHelp, same as the deleted web component; `label ??` override at :41; test 3 |
| 2 | yes | es.json `Confianza alta` / `Confianza media: pruébalo` / `No hay suficientes datos` byte-identical to web's old `market.band.*` |
| 3 | yes | 3 tests: three bands' text, icon `aria-hidden`, override replaces default text |
| 4 | yes (adjusted) | ui has no `build` script (source package via `link:`); consumer builds (web by me, web+floor by author) stand in, per CLAUDE.md DoD table |

## Blocking findings
none

## Checks
- [x] Only owned paths changed: 7 files, all in the card's list plus `playground/App.tsx` (tech lead grant, wave.md build log 2026-10-01)
- [x] Nothing outside scope (no vote card, no other component)
- [x] Tests exercise the behavior and fail without the change; nothing weakened
- [x] Tenancy/idempotency/money: n/a (presentational); en and es strings present
- [x] Decisions: architect R2 followed (`src/app/`, contracts `ConfidenceBand`, `confidenceBand.*`); `interface` instead of `type` alias is equivalent

## Optional notes (not blocking)
- The tests do not pin the tone per band: swapping `BAND_VARIANT.high` and `.low` would still pass. A `toHaveAttribute("data-variant", …)` or class assertion per band would lock the "same look" claim.
- No kit test renders Spanish; Spanish is proven only by the catalog diff (and the web path in T-P7-3's review).
