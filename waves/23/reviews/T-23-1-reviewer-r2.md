# Review of T-23-1 (round 2)

- Reviewer: reviewer on Opus 5.5 · Author: web-engineer on Opus 5.5 · Diff: invai-web `353a49d..34a8fd2` (6f5dbe7, 34a8fd2)
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| Own flatten script (node strip-types) on en/es at 54b64d7, 353a49d, 34a8fd2 | 1953 base keys, 0 missing from HEAD en or es. 0 keys whose base Spanish differs at HEAD. es==en: 39 at base, 39 at HEAD, same set, 0 new. HEAD has 2017 keys (64 new); 0 new keys with es==en |
| New keys read by hand (64) | Real Spanish, placeholders kept (`{{n}}`, `{{name}}`, `{{time}}`). The 10 changed since r1 (`action.*`, `common.loading/noResults`, `adSpend.subtitle`, `po.markPlacedHint`, `stock.submitCount`) now translated |
| `gen-i18n.py` + `biome format` on a scratch `git archive 34a8fd2` | `src/i18n` output byte-identical to committed; no `i18n-es-missing.json` written. The ignored one in the worktree is stale |
| `pnpm typecheck` / `pnpm lint` | 0 errors / 1 pre-existing warning (`markdown.test.ts`) |
| `pnpm test --reporter=dot` | 19 files, 119 tests passed |
| `VITE_API_URL=http://localhost:3000 pnpm build` | built; largest `vendor-*.js` 394.98 kB, no >500 kB warning |
| `scan-test-weakening.sh invai-web 353a49d` | no hits. `git status --short` clean |

## Acceptance criteria
AC1–7, 9, 10 as in r1 (unchanged code paths). AC8: **yes now**. No Spanish lost, no new English fallbacks (proof above). AC6 billing money: 3 `<Money>` changed to `formatMoney(…, digestMoneyLang(i18n.language))`, same es-US helper the page already uses for counts; `i18n` is in scope at both call sites (lines 56, 468).

## Scope
Diff touches only `scripts/i18n-es.json`, `scripts/i18n-extra-en.json`, `src/i18n/{en,es}.ts`, `billing.tsx` (3 money spans plus import) and `shipping.tsx` (TabsList wrapped in the `overflow-x-auto` div already used in `orders/index.tsx`). `extra-en` only adds dynamic keys and removes none. No other files.

## Blocking findings
None.

## Checks
- [x] Owned paths only · [x] no weakened tests · [x] en/es complete · [x] no tenancy, idempotency or money-math change (formatting only, integer cents in)

## Optional notes (not blocking)
- `gen-i18n.py` prints "extra es keys" (`assistant.q1-5`, `listings.highRisk*`). These keys were there before this card and are harmless.
- r1 notes (resend button vs `delivery`, redundant `RATE_EXPIRED` silence) still stand as optional.
