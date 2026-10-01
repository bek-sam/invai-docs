# Review of T-P7-3 (round 1)

- Reviewer: reviewer on claude-opus-5-5
- Author: web-engineer on Claude Opus 5.5 (card says sonnet)
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `invai-web`: `pnpm typecheck && pnpm lint && pnpm test --reporter=dot && VITE_API_URL=http://localhost:3000 pnpm build` | exit 0; 24 files, 163/163; lint 1 pre-existing warning; built (my `dist/` removed after) |
| `-assistant.test.ts` against base (`git archive f20021b~1` + copied test) | 5/5 FAIL (`assistantErrorMessage is not a function`) |
| `scan-test-weakening.sh invai-web f20021b~1` | only hits are qa-engineer's uncommitted `e2e/**` (not in f20021b, whose stat has no e2e path); new test adds asserts, removes none |
| Kit Spanish inside web: read `src/i18n/index.ts:18-22` + bundle grep | see AC2 |
| `grep -rn market.band invai-web/{src,scripts,e2e}` | no hits left |
| Mapping vs `invai-backend/src/modules/ai/service.ts:1320-1328` | matches (below) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `recommendation-card.tsx:2` imports kit `ConfidenceBadge`; local file deleted; no importer left; digest `insight-card` reuses `RecommendationCard` |
| 2 | yes | How kit text reaches web: `initAppI18n` calls kit `initI18n` (loads `locales/{en,es}.json` into the `translation` namespace), then `addResourceBundle(..., deep=true, overwrite=true)` merges web keys on top, so `confidenceBand.*` survives. One i18next: `vite.config.ts:69-73` dedupes `i18next`/`react-i18next`; the build has one `vendor-i18n` chunk and `Confianza media: pruébalo` only in `index-*.js` (kit JSON). Same path already serves kit-only keys in prod: web has no `orderState.*`/`dataTable.*` keys, `StatusBadge` reads kit `orderState.*`. Text byte-identical (python diff), tones/icons identical. My SSR render probe could not run in node vitest (two React copies outside Vite's dedupe), so this is static + bundle proof; the gate screen look is the live check |
| 3 | yes | above; `recommendation-copy.test.ts` untouched and green |
| 4 | deferred | :3000 down; card allows the gate fallback. Tech lead must look at market en/es 1440/390 at the gate |
| 5 | yes | backend: `CREDITS_EXHAUSTED`→`credits_exhausted`, `AI_SPEND_CAP_REACHED`→`spend_cap`, "declined"→`refusal`, else `internal`; web `assistant.tsx:29-49` maps all four, default keeps `message` (contract enum also has `rate_limited`, server text kept). es keys typed via `Messages`; `i18n-es.json` in sync. 5 tests incl. unknown + missing |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (8 files; `-assistant.test.ts` is the AC5 test, route-ignored dash prefix like `-index.test.ts`)
- [x] Nothing outside scope; `e2e/**` and `invai-ui/**` untouched by f20021b
- [x] Tests fail without the change; none weakened
- [x] Tenancy/idempotency/money n/a; en and es strings present, tú form (`Inténtalo`, `Vuelve`, `pídele`)
- [x] Decisions: drop-keys vs `label` choice stated in report, as AC2 asks

## Optional notes (not blocking)
- `assistant.error.spendCap` says "ask the owner to raise it", but the cap is `AI_DAILY_TENANT_CAP_CENTS`/platform env (`breaker.ts:44-48`); no shop owner can raise it, and a platform-scope hit is not "your shop's" limit. The card's example wording invited this; suggest "Try again tomorrow." only. Tech lead's call.
- es uses "propietario" (only use in `es.ts`); the catalog says "dueño" everywhere else (`es.ts:360,947,2628`).
- Spend-cap/credits tests use `toContain("today"/"credits")` on the defaults; they don't check the key names. Typecheck covers key existence.
