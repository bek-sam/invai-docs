# Report: QA acceptance tests, wave 26 (listing photos, phase A)
Author: qa-engineer on Opus 5.5

## Built
- `invai-backend/src/modules/photos/photos.acceptance.test.ts` (new, QA-owned): T-26-4 ACs 2-8
  through the service/router, independent of the author's own `photos.test.ts`, with a fake
  imaging client (vi.spyOn on `imaging`, same seam the module's unit tests use).
- `invai-web/e2e/listing-photos.spec.ts` (new, QA-owned): T-26-5 ACs 1-6 browser flow.
- `invai-web/e2e/screens.smoke.spec.ts`: added `/listing-photos` to `SHOP_ROUTES`.

## Results
- Backend: `OPENAI_API_KEY= ANTHROPIC_API_KEY= pnpm vitest run --reporter=dot
  src/modules/photos/photos.acceptance.test.ts` → **16/16 passed**, 3.5s (backend already built,
  commits 30618a0/5930d59 — no product bug found; all 16 cases went green first try).
  ("close timed out ... Vite servers not exiting" after is a known benign teardown quirk, not a
  test failure — logged previously in qa-engineer memory.)
- Web: `pnpm exec tsc --noEmit -p .` → clean (no errors). `biome lint` on both touched files →
  clean. No browser run yet (T-26-5 hasn't built the route); the spec is expected red at the
  integration gate until then, per instructions.

## Coverage (T-26-4 ACs → tests)
| AC | Test |
|---|---|
| 2 analyze pending→ready, contrast in code | `AC2: analyzeDesign is pending, then ready via the job...` (+ NOT_FOUND for another company's design) |
| 3 estimate/createSet | `AC3: estimate counts...` / `createSet is idempotent on idempotencyKey...` |
| 4 CREDITS_EXHAUSTED before rows | `AC4: CREDITS_EXHAUSTED refuses before any row is written` |
| 4/9 charge once per composition on retry | `AC4/9: a render job run twice charges...` (+ imaging-down case) |
| 5/6 approval gate | `AC5/AC6: approval gates zip and attach` |
| 7 attach flags/keys | `AC7: attach sends the approved images' keys with phase-A flags false/false` (+ foreign draft NOT_FOUND) |
| 8 signed URLs | `AC8: signed URLs never cross a company prefix...` |
| role access | `office allowed` / `presser FORBIDDEN` / `another company's set id NOT_FOUND` via `router.photos.*` |

## Web spec notes for T-26-5
- Route assumed `/listing-photos`; nav link text "Listing photos"; flagged to web-engineer in the
  commit message so the built route matches.
- Selectors follow the card's own wording (e.g. "Generate", "Approve all passing", "Download zip",
  "Attach to AI listing draft", garment/color/view/channel checkbox labels) — the web-engineer may
  need to adjust copy to match exactly, or ask QA to adjust selectors if copy differs for a good
  reason.
- Presser case signs in with `presser@desertbloom.test` / `demo1234!` (per CLAUDE.md seed logins)
  and checks both no nav link and a no-access page at the route — this is the first web screen
  gated this precisely, so there's no existing "no-access page" pattern to copy; web-engineer picks
  the exact text, this spec matches loosely (`/don't have access|no access|not authorized/i`).

## Known gaps and follow-ups
- Web E2E not run in a browser (no servers started, per instructions); will run at the T-26-5 gate.
- Held-back cases: none held back separately this round — the full set above was handed over, since
  the card's own unit tests already cover much of the same ground independently (reviewed, not
  duplicated).

## Blocked by other owners
- None.

## Processes and data
- No processes started; no servers run. Shared dev DB untouched.
