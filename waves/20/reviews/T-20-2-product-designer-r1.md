# Review of T-20-2 (round 1)

- Reviewer: product-designer on Sonnet 5
- Author: web-engineer on Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web show f59438f --stat` | 11 files, all inside owned paths (digest components/routes, errors.ts FORBIDDEN case, the recommendation-copy.ts grant, i18n) |
| Read all 4 screenshots in `waves/20/reports/shots/` | Looked at each, described below |
| `node -e "new Intl.NumberFormat('es').format(1950/9999/10000)"` | `1950`, `9999`, `10.000` — confirms the report's claim that `es` groups only from 5 digits is real CLDR behavior, not a bug |
| `grep -n "R1 action (peak under way" invai-docs/specs/market-signals.md` | Exact en/es strings match the shipped `market.action.r1UnderWay` keys verbatim |
| `grep -n "PTS_LOCALE" invai-backend/src/modules/digest/facts.ts` | Confirms the Spanish points comma comes from a **backend** file (T-20-1's owned path), not from anything in this diff |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Spanish heading | Yes | `t20-2-digest-detail-es-390.png`: "Semana del lun 21 de sep", no English weekday/month tokens |
| 2 Points/unchanged, no arrow | Yes (as the card literally specifies — see note below) | Glance grid: "Margen 31.4% ↑ +3,3 pts" (green arrow, comma decimal), "Tasa de puntualidad 100% sin cambio" (no arrow, muted gray, no color-only signal) |
| 3 Refused page | Yes | `t20-2-notifications-forbidden-office-en.png`: "No access / You don't have access to this page. Ask the owner." — plain, actionable, no raw permission string, no internal words |
| 4 Thousands separator | Yes (digest page, within owned scope) | `t20-2-plan-usage-es.png`: "387 de 10.000 pedidos ... 1950 créditos de IA" — correct; en screenshot shows "10,000" |
| 5 R1 peak-under-way wording | Yes | en/es strings in the diff match `specs/market-signals.md` line 214 verbatim |
| 6 390/1440, en/es, no raw keys, ≥44px targets | Yes | No raw keys or English-in-Spanish seen in any of the 4 shots; 390px es shot has no overflow/truncation; no new interactive control was added by this diff (`GlanceTile`'s delta text is static, not a target), so the ≥44px rule isn't newly at risk here |

## Blocking findings
None inside this card's owned paths.

## Cross-card issue found (not a T-20-2 defect — flagging for the tech lead / T-20-1)
`invai-backend/src/modules/digest/facts.ts:90` (`PTS_LOCALE: { en: "en-US", es: "es" }`) still formats Spanish points with a **decimal comma** ("+3,3 pts"), which is exactly what the shipped screenshot shows. But `specs/weekly-digest.md`'s "Change wording" note (added 2026-09-28, same day, in the product-manager's T-20-1 round-1 co-review) explicitly overturned that: *"one convention for the whole digest, `es-US` throughout, including points — '+6.9 pts' in Spanish too... One rendered line never mixes separators."* The live Spanish tile does mix separators today: **"31.4%" (period) next to "+3,3 pts" (comma)** in the same Margen tile — the exact failure mode the spec correction was written to prevent.

This is not a T-20-2 defect: the web only renders `item.change.formatted[lang]` verbatim (card's "Depends on" line), and `facts.ts` is T-20-1's owned file, not this card's. I also note the T-20-2 card's own AC2 text still quotes the *old*, now-superseded example ("+6.9 pts" / "+6,9 pts") — it wasn't updated after the spec's correction, so the author built exactly what the card asked for. Recommend the tech lead: (1) get T-20-1's round-2 fix (switch `PTS_LOCALE.es` to `es-US`) landed before the wave 20 gate, since a mixed-separator Spanish number is a real plain-language defect a shop owner will see, and (2) correct T-20-2's card text to match. No web change is needed once the backend fix lands — `glanceChangeDirection` and `GlanceTile` will render whatever period-formatted string arrives correctly, since neither owns the number formatting.

## StatCard neutral-state gap (decision, as asked)
Confirmed: `@invai/ui`'s `StatCard` always draws an arrow whenever `delta` is set — `deltaDirection` only selects color/icon, there's no "no direction" value. Building a local `GlanceTile` on the `Card` primitive to get the neutral "unchanged"/"sin cambio" state (no arrow, muted text, still readable without color alone) is **acceptable for now**: it follows the documented pattern for a missing kit capability (build locally, report the gap), matches `StatCard`'s visual language, and correctly satisfies AC2/AC6 (color + icon + text, never color alone). I will add a neutral/no-arrow `deltaDirection` variant to `StatCard` as a follow-up `invai-ui` task on my own backlog (not done in this review) so future consumers — this glance grid included — can drop the local copy.

## Checks
- [x] Only owned paths changed (`git diff --stat` — all 11 files inside `src/components/digest/**`, `src/routes/_app/digests/**`, `src/lib/errors.ts` FORBIDDEN case, the `recommendation-copy.ts` grant, `src/i18n/{en,es}.ts`)
- [x] Nothing outside scope (test-fixture fixes for the two files above are co-located tests for owned code, flagged transparently by the author per `respect-ownership`)
- [x] Tests exercise the behavior; no `.skip`/loosened assertions/mocked-unit-under-test seen in the diff
- [x] en/es text: plain language, matches glossary and the approved spec copy rows verbatim (except the backend-owned pts-comma issue above, which is outside this diff)
- [x] Decisions recorded where needed (author's report documents the `GlanceTile` and locale choices)

## Optional notes (not blocking)
- The Notifications "No access" screen still shows a "Retry" button (from the pre-existing `ErrorState` component, not touched by this diff). Retrying a permission error won't help; consider whether `ErrorState` should suppress or relabel the retry action for `FORBIDDEN` specifically. Not this card's scope (that component lives in `invai-web/src/components/states.tsx`); noting for whoever next touches it.
- Dark mode was checked live per the report but not captured in a screenshot; fine for this card's "at most 4 screenshots" budget, but a future card touching the glance grid should save one dark-mode shot given the new color-token usage in `GlanceTile`.
