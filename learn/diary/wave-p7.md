# Wave P7 — a repeatable gate pool, one shared confidence badge, tighter guard hooks, a per-round AI spend check

**Dates:** 2026-10-01.

## What was built
- **T-P7-1** The golden-path suites hold the mock Shopify auto-import while they run
  (B-255) (qa-engineer) — so a mock order can't land mid-run and change the numbers a
  suite is checking.
- **T-P7-2** Shared `ConfidenceBadge` in `invai-ui` (B-134, kit half) (product-designer) —
  one component, not several copies, for showing confidence on a market/assistant answer.
- **T-P7-3** Market screens use the kit badge; local copy removed (B-134, web half);
  assistant spend-cap message in en/es (B-262) (web-engineer).
- **T-P7-4** Guard reads scripts it runs, blocks `sst secret` and repo-setting API calls;
  Stop check counts shell edits (B-115, B-189) (platform-sre) — **not approved** this
  round; escalated as OI-23.
- **T-P7-5** The assistant re-checks the spend caps before every tool round and records
  spend per round (B-115) (ai-engineer) — one assistant question can no longer run past
  the shop's or the platform's AI spend cap mid-conversation.

## Why
By this point in the project, the gate, the shared UI kit and the guard hooks are all
mature enough that *polishing the team's own tools* is as real a task as polishing the
product — a flaky gate (mock orders landing mid-run) or a guard with a gap is exactly as
damaging to velocity as a product bug.

## What went wrong
- A full backend suite exited with code 1 once, and the actual cause was lost — the
  token-budget rule said only "end with `tail -n 40`," which keeps a short summary but
  drops the specific failing test names and, without `pipefail`, even masks the exit code
  itself.
- T-P7-4's round 2 fixed the guard's real blocking finding but also added optional extras
  in the same round — one of those extras introduced a regression that failed the round
  and escalated the whole card, because the round 2 prompt had asked for the blocker
  *and* the optional items together, exposing brand-new code to its first security
  review only at the project's last allowed review round.
- A card's example user-facing copy ("ask the owner to raise it") turned out to be wrong,
  because the limit it referred to is actually a server setting, not something the owner
  can change from a screen — nobody had checked where the setting actually lived before
  writing the example.

## What the team learned
- Full test-suite runs use `set -o pipefail`, write to a log file, then grep for
  FAIL/Error lines plus the tail — a bare `tail -n 40` on its own can hide both the real
  failure and a non-zero exit code.
- A review round fixes only the blocking findings; optional extras go to the backlog or a
  new card, never bundled into the same round as a blocker — new code shouldn't meet its
  first security review at the last round a card is allowed.
- Before writing example copy on a card, check which role can actually change the thing
  the copy points to.

## Files to look at
- `invai-web/e2e/` (mock-import hold) — T-P7-1.
- `invai-ui/src/components/ConfidenceBadge.tsx` — T-P7-2.
- `invai-web/src/components/market/` (badge adoption, spend-cap message) — T-P7-3.
- `invai-docs/team/hooks/guard-bash.py` — the still-escalated T-P7-4 (OI-23).
- `invai-backend/src/ai/gateway.ts`, `src/ai/credits.ts` — per-round spend check (T-P7-5).
- `invai-docs/owner-inbox.md` (OI-23).
- `invai-docs/team/lessons.md` (2026-10-01, "wave P7" rows, three of them).
