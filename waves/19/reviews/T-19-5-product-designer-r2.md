# Review of T-19-5 (round 2)

- Reviewer: product-designer on sonnet
- Author: web-engineer on sonnet
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| Read my round-1 file (blocked on D8 win headline, D3 raw `costLine`) | restated both as observable results before reading the fix |
| `git -C invai-web show 87e800d` | `digestWinText` now branches on the real wire `templateKey === "D8 win"` and reads `insight.facts` (`d8.net`/`d8.weeks` vs `d8.onTimeRate`) instead of the invented `win.best_net_week`/`win.on_time_record` keys; `digestActionText`'s `review_costs` case now calls new `costLineLabel()` against `digest.costLine.*` instead of interpolating `params.costLine` raw; `sourceDateText` now takes `lang` |
| `grep -n "D8 win.bestNet\|D8 win.onTime\|costLine\." invai-backend/src/modules/digest/render.ts` | backend text: `"Your best net week in {{n}} weeks: {{net}}"` / `"Tu mejor semana neta en {{n}} semanas: {{net}}"`; `"Your best on-time rate yet: {{rate}}"` / `"Tu mejor tasa de envíos a tiempo: {{rate}}"`; 8 `costLine.*` pairs (`channelFees`→"channel fee"/"comisiones del canal", …) |
| `grep -n "win:" invai-web/src/i18n/en.ts invai-web/src/i18n/es.ts` (read the diff directly) | web's `digest.win.bestNetWeek`/`onTimeRecord` and `digest.costLine.*` (8 keys, en+es) are verbatim identical strings to the backend's `render.ts` table — word-for-word, not just meaning |
| Read `invai-docs/specs/weekly-digest.md` (D3/D8 rows, Copy table) | spec gives D3 `"Review {{costLine}} costs"` with the placeholder unresolved and D8 only "none (celebrate)" with no exact win wording — the spec leaves both to match the backend's own render, which this fix now does |
| `git -C invai-backend show cfe1098` (T-19-3 r2) | R1's empty-`{{channels}}` fix now falls back to `market.channels.connected`: `"your connected channels"` / `"tus canales conectados"` |
| `grep -n "connected" invai-web/src/components/market/recommendation-copy.ts invai-web/src/i18n/{en,es}.ts` | web's own `market.channels.connected` (T-18-5, unmodified) is the identical phrase in both languages — the two repos now agree |
| `git -C invai-web diff --stat origin/main` | round-2 commit touches only `src/components/digest/digest-copy.ts`, `digest-copy.test.ts` (new), `insight-card.tsx`, `src/i18n/en.ts`, `src/i18n/es.ts` — all inside the card's owned globs |
| Read `digest-copy.test.ts` | 5 cases for `digestWinText` (real key + facts, on-time-only, es uses fact's own formatted value not browser locale, wrong key falls back, `"D8 win"` with no facts falls back) and cases for `review_costs` (named example, all 8 values, unknown value still gets a real word, never the identifier) |

I did not restart the app; both fixes are pure-function copy logic fully covered by the new unit tests, and I verified the backend-side strings by reading `render.ts` directly rather than trusting the report's claim of a verbatim match.

## Acceptance criteria (the two I blocked on)
| # | Met? | Evidence |
|---|---|---|
| 2 Digest page — the win shows its number | yes | `digestWinText` reads `facts` and interpolates `n`/`net` or `rate`; matches backend wording exactly, en and es |
| 7 en/es, no raw keys | yes | `costLineLabel()` maps all 8 `CostLine` values to the same plain words the backend already uses; an unrecognized value falls back to a real English word via the local map, never the bare identifier |

## Blocking findings
None.

## T-19-3 round-2 copy check
The new "your connected channels" / "tus canales conectados" fallback (`invai-backend` commit
`cfe1098`) is plain, shop-appropriate language, not an internal term, and it is not new
vocabulary: it's a byte-for-byte match of web's existing `market.channels.connected` string from
T-18-5. Same phrase, same meaning, in both languages, in both repos — consistent and correct.

## Checks
- [x] Only owned paths changed (`git diff --stat` above)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, none weakened — new `digest-copy.test.ts` covers exactly the
  two behaviors I blocked on, plus the `sourceDateText` locale fix; no existing test loosened
- [x] Tenancy/idempotency/money — n/a (no server code this round); en/es complete and now
  verbatim-matched to the backend's own copy for D8 and D3
- [x] Decisions recorded where needed — n/a; the market-watch backend bug is correctly reported
  under "Blocked by other owners" rather than edited (out of this card's paths)

## Optional notes (not blocking)
1. Round 1's optional notes (`format.ts`'s browser-locale `formatDay()`/`toLocaleDateString`) are
   unchanged and still correctly disclosed as out of this card's paths — not re-raised here.
2. Nice touch: `digestWinText`'s number now comes straight from the fact's own `formatted[lang]`
   string already on the wire, so web never re-implements money/rate formatting — one less place
   for en/es or rounding drift to creep in later.
