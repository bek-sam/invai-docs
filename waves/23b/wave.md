# Wave 23b: P2 sweep, part 2b: imaging, AI polish and E2E coverage

- Split from wave 23 on 2026-09-29 (owner approved T-23-6 and T-23-7, and the 5-card cap applies). Card files stay in `waves/23/` under the same ids. Plan reviews as for wave 23 (PM and architect, 2026-09-28). Decision 0019 co-reviewer cuts are already applied.
- Runs after wave 23's gate, and before or alongside analytics A1, as the PM ranks it.

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| T-23-3 Imaging polish and film-use metric (B-103 rest, B-41) | imaging-engineer | sonnet | reviewer (opus) + architect (bounds in contract) | files | planned |
| T-23-4 AI and market polish: markdown and footer, stream close, mock follow-ups, eval cleanup, detrended seasonality in code, shared ConfidenceBadge adoption (B-114, B-131, B-132, B-135, B-165; B-134 via a product-designer grant) | ai-engineer (+ backend-engineer market for the B-131 engine by grant; never `specs/**`) | sonnet | reviewer (sonnet) | ai | planned |
| T-23-8 A fresh seed builds this week's digest (B-207; bug, pulled forward: blocks the push gate) | backend-foundation | sonnet | reviewer (opus) | none | approved r1 (runs in wave 23; push with wave 23's gate) |
| T-23-5 E2E and test coverage: roles, Spanish, offline replay, clickIfShown, property tests, axe, visual regression, runtime contract test, i18n drift, scale seed profiles, market tool latency (B-22 rest, B-34, B-38, B-97 rest, B-138, B-142) | qa-engineer | sonnet | reviewer (opus) | — | planned |

## Integration gate
- [ ] `pnpm gate` (T-23-6) passes on a fresh seed; screens looked at in en/es
- [ ] Pushed to `main`

## Team metrics
| First-pass approvals | Canary caught? | Escaped defects | Reopened | Avg cycle time | Tokens per card |
|---|---|---|---|---|---|

## Handoff from wave 23 (2026-09-30, tech lead)
- **State:** every wave 23 card except T-23-6 is approved, with reviews in `waves/23/reviews/`, and T-23-8 is approved too. **Nothing from wave 23 is pushed.** The live push hook needs a full `pnpm gate` pass on the same SHAs, and the last run (`invai-infra/.gate/run-20260930T030247Z.log`) had 2 browser failures that are spec-harness issues, not product bugs. Don't bypass the hook and don't skip or weaken specs.
- **Unpushed SHAs, all approved:** contracts `7ee15b6`; ui `952c174`; backend `032b9f6` (T-23-7, T-23-0 `d39a481`+`6510860`, T-23-8); web `34a8fd2` (T-24-1 `c1d53a8`, cleared for the web push by the 2026-09-30 ruling in `waves/24/wave.md`; T-23-7; T-23-1); floor `7900d0a` (T-23-7, T-23-2); imaging `58b67ee`. Docs have uncommitted reports, reviews, backlog B-209..B-218, 4 lessons and the agent-brief change: commit them first.
- **Hold:** infra (`3dbb899` T-24-1 needs S-45 fixed; `b62ad92`/`3215fc6` T-23-6 wait for OI-22; `9fe0c55`/`490884d` T-23-7 sit on top). Until infra is pushed, the dispatch-only E2E workflows can't find `scripts/ci/run-e2e.sh`.
- **Step 1, the push (small, do it first):**
  1. T-23-9 (qa-engineer, sonnet; `invai-web/e2e/**`; reviewer opus). `digest-dates.spec.ts:52` must wait for the detail heading itself (for example, expect the `h1` to match the ES pattern) instead of reading `h1` straight after `settled()`. Also find what `market.spec.ts:91` ("Sample data" badge) needs on a plain fresh seed.
  2. If the market fix needs the seed, add T-23-10 (backend-foundation, sonnet; `src/db/seed/**`, the same pattern as T-23-8's digest).
  3. Then `pnpm gate invai-contracts invai-ui invai-backend invai-web invai-floor invai-imaging` (in the background, about 25 min; it refuses while anyone else uses `invai_test`), then push those six repos plus docs.
- **Cap:** T-23-8, T-23-9 and T-23-10 take 3 of the 5 slots. So T-23-3 and T-23-4 stay, and T-23-5 (E2E coverage, the largest card) moves to wave 25, as the wave 23 build log planned. The PM confirms this.
- **Owner:** OI-21 (CI read token), OI-22 (T-23-6 round 3). Don't touch T-23-6 until they're answered.
- **Gate also owes:** looking at the floor screens at 1280×800 in en and es. T-23-2's designer checked by code trace only, and the author's screenshots weren't on disk.
- **Backlog from wave 23:** B-206 (alert kind plus T-23-1 AC9's Spanish alert text), B-208 (sheet race), B-209..B-218 (thumbnails Medium; the rest Low); S-43 and S-45 are in `security/v1-review.md`.
- **Environment:** :3142 (PID 98947) and vite :5183 (PID 73962) are unknown and older than this session; leave them alone. There are idle `tail -f` processes from agents (10572, 61568, 61661). The dev DB is freshly seeded by the 03:03 UTC gate.

