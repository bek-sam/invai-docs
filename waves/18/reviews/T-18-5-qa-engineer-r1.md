# Review of T-18-5 (round 1)

- Reviewer: qa-engineer on Opus 5.5
- Author: web-engineer on Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web diff --stat ab961f3~1 ab961f3` | 12 files, all inside T-18-5's owned globs (`src/routes/_app/assistant.tsx`, `.../catalog/designs.$designId.tsx`, `src/i18n/{en,es}.ts`, `src/components/market/**`) |
| `git -C invai-web log --oneline origin/main..HEAD` | `ab961f3`, `01ec8cb` (QA's own commit) — not pushed |
| `pnpm typecheck` (invai-web) | clean |
| `pnpm lint` (invai-web, `biome check .`) | "Checked 154 files. No fixes applied." |
| `pnpm test` (invai-web) | 88 passed (16 files), incl. the 6 new `recommendation-copy.test.ts` cases |
| `pnpm build` (pre-built by the author with `VITE_API_URL=http://localhost:3162`, confirmed by grep of the built bundle) + served with `vite preview --port 5195` | serves 200, app loads |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-web ab961f3~1` | one "removed assertion" hit, which is my own uncommitted `e2e/market.spec.ts` edit (moved, not deleted — see below); nothing in T-18-5's own paths |
| curl (own script), `designer@desertbloom.test` → `market.recommendations.list` | `403 FORBIDDEN`, `"Missing permission finance.read for market.recommendations.list"` |
| curl (own script), `designer@desertbloom.test` → `market.niches.taxonomy` | `200`, 69 taxonomy items (designer has `catalog.read`) |
| `E2E_WEB_URL=http://localhost:5195 E2E_API_URL=http://localhost:3162 pnpm e2e e2e/market.spec.ts` (my API on 3162 against `invai_t18_qa_dev`, Redis DB 15, web built for 3162 and served by `vite preview` on 5195) — run per acceptance criterion (see below) | all 5 tests pass in isolation; see "Known gaps" for why a single unbroken 5-test run currently trips a pre-existing, unrelated rate limit |

Setup: reused `invai_t18_qa_dev` (28/28 migrations, matches `invai-backend` HEAD `0bc68e2`; already carries 22 `market_recommendations` rows from the market jobs run by an earlier session). API `PORT=3162` against that DB, `REDIS_URL=redis://localhost:6379/15`, `MOCK_CARRIER_TRANSIT_HOURS=0.001`. Web: the pre-built `invai-web-t18-qa` worktree's `dist/` (already targets `:3162`), served with `VITE_API_URL=http://localhost:3162 vite preview --port 5195 --strictPort` (`vite preview`, not `vite dev`, for the same CSP reason the author's report documents — `vite.config.ts`'s dev-mode CSP hardcodes `localhost:3000`).

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| AC2/AC30 chips, badge, votes render from the stream | Yes | `market.spec.ts:90` green in isolation: "Market trend" chip, "Sample data" badge, source+date text, `done`/`not useful` buttons with matching counts, `rec.sample` sentence, confidence band text |
| AC15 Spanish | Yes | `market.spec.ts:171` green in isolation (after my locator-order fix, see below): "Tendencia del mercado", "Datos de muestra", no English leakage, no unpaired vote buttons |
| AC27/AC33 vote idempotent + survives reload | Yes | `market.spec.ts:128` green in isolation: `aria-pressed` set on first tap, unchanged `votedAt` on a second tap, still pressed after `page.reload()` + reopening the conversation from the sidebar |
| AC32 niche chip 0/1/2, one picker, refuses a third | Yes | `market.spec.ts:196` green (verified with a throwaway copy that additionally ignores the `vite preview`-only MinIO-image CSP noise below; the niche logic itself has no dependency on that noise) |
| AC24 / T-18-5 AC6 designer sees niche but no votes/prices | Yes | `market.spec.ts:263` green (same throwaway-copy note as AC32) |
| Permissions in UI | Yes | curl above (403 for `finance.read`-gated `recommendations.list`, 200 for `catalog.read`-gated `niches.taxonomy`), matching the report's designer screenshot description |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat ab961f3~1 ab961f3`: all 12 files inside T-18-5's grant)
- [x] Nothing outside scope (no contract, backend or `@invai/ui` edits; local `ConfidenceBadge` correctly flagged by the author as a promotion candidate, not built where it doesn't belong)
- [x] Tests exercise the behavior; the scan script's one hit is my own e2e-helper edit (reordered, not weakened — see Known gaps); T-18-5's own new test file (`recommendation-copy.test.ts`) is all additions
- [x] Tenancy n/a (no new procedures/tables in this card); money n/a (no cents fields touched); en/es text present and checked live in both languages by the author and again by me (curl + the Spanish e2e test)
- [x] Decisions: the author's three (`vite preview` for manual verification, fetching full records via `list({ids})`, one combined-text niche badge) are sound and documented in the report; no cross-cutting decision needed from me

## Known gaps (not blocking T-18-5; filed elsewhere)
1. **A pre-existing per-company `ai` rate-limit bucket (`RATE_BUCKET_LIMITS.ai` = 20/min, `invai-backend/src/lib/ratelimit.ts`; `bucketFor()` in `src/api/orpc.ts` routes *every* `ai.*` path there, including the cheap `ai.credits.balance` and `ai.assistant.conversations` reads, not just `ai.assistant.ask`) trips under normal, legitimate serial use of the new multi-starter assistant UX.** Reproduced directly: two market e2e tests in a row (each: one page load = 2 reads, one-to-three `ask()` calls each followed by a `conversations` invalidate) were enough to exhaust the bucket, and the third test's own initial `/assistant` load then got `429` on `ai.credits.balance`, rendered to the user as the untranslated string "Too many requests" (no i18n mapping for `RATE_LIMITED` in `invai-web/src`). This is unrelated to T-18-5's diff (T-18-5 didn't touch `orpc.ts` or `ratelimit.ts`; the bucket and its `ai.*` classification predate wave 18, T-12-3/B-20) — filed for the tech lead to card to backend-foundation/architect: either give reads under `ai.*` the `reads` bucket, or size the `ai` bucket for a real multi-question chat session. I mitigated this in my own `firstAnswerWithVotes` (see below) enough to get each test green in isolation, but a single unbroken 5-test run of `e2e/market.spec.ts` can still exhaust it — that's an environment/backend-capacity fact, not something I can fix by editing my own test file further, and not something to paper over with a sleep or a loosened assertion.
2. **Running my exact port-isolated verification stack (`vite preview` + local MinIO over plain `http://localhost:9000`) trips the niche tests' `watchPage` CSP check on the design's thumbnail image**, because `vite.config.ts`'s `prodCsp` allows `img-src ... https:` but not `http:` (the *dev* CSP explicitly allows `http://localhost:9000`, which is why `pnpm dev`/`pnpm e2e` on the standard `:5173`/`:3000` stack won't see this). This is the same `vite preview`-for-a-non-default-port tradeoff the author's own report already names in "Decisions" — I confirmed it's cosmetic to my verification method, not a defect, by rerunning AC32/AC24 with only that one CSP pattern additionally ignored (throwaway copy, not committed): both pass clean otherwise. No card needed; noted for whoever gives every wave agent its own real dev-mode port.

## Fixes I made in my own owned paths (`e2e/helpers/ui.ts`, `e2e/market.spec.ts`) while finishing the QA follow-ups from `wave.md`
- `loginAs` accepts either the English or Spanish field/button labels (Spanish login page shows "Correo"/"Contraseña" once `invai.lang=es` is set before navigating there).
- `starterButton`/`askStarter` are scoped to the true chat pane and match exactly, so a starter pill's text no longer collides with a same-titled sidebar history entry.
- `watchPage` allow-lists exactly `POST /rpc/ai/assistant/ask` + `net::ERR_ABORTED`, and only for a request this same `watchPage` instance already saw complete with `200` (comment points to B-132; every other failure, including a status-200-then-non-`ERR_ABORTED` failure or an abort with no prior 200, still fails the test).
- The niche test clears the target design's niches via the API before opening the picker, so the "pick two, refuse a third" assertions don't depend on what the nightly classifier already did to the seed's first-listed design.
- Beyond those four: `firstAnswerWithVotes` now tries the one starter that reliably yields votes on this seed first instead of looping through the other two every time (cuts the suite's own `ai`-bucket footprint roughly in half — see Known gaps #1); and the Spanish test's "another starter's pill is still in Spanish" check now runs *before* the first message is sent, since the empty-state pills it's checking are replaced by the chat history right after (this ordering bug was independent of my other fixes — it was never exercised before, since the suite never got past test 2 in earlier runs).

## Optional notes (not blocking)
- Recommend the product-designer's suggested promotion of the local `ConfidenceBadge` into `@invai/ui` happen before wave 19's digest needs the same treatment (already flagged in the author's own report).
