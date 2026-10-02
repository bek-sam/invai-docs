# Wave 13 — contracts and quality

**Dates:** late September 2026, after wave 12.

## What was built
- **T-13-1** Floor API version handshake (architect + floor-engineer + backend-foundation):
  an old, un-updated floor tablet gets a clear `CLIENT_TOO_OLD` error instead of silently
  corrupting data against a contract it no longer matches after a deploy.
- **T-13-2** Contract CI and versioning (architect + platform-sre): every change to
  `@invai/contracts` bumps its version and is checked by CI against every consumer repo
  automatically, not by memory.
- **T-13-3** Contract drift cleanup (architect): dead or undelivered parts of the contract
  (procedures nothing calls, fields nothing fills) are removed.
- **T-13-4** E2E coverage and CI (qa-engineer): role-based tests, Spanish-language tests,
  property-based tests and accessibility (axe) checks all added to CI, across web, floor
  and backend.
- **T-13-5** Realistic seed efficiency (backend-foundation): the demo seed runs fast
  (~25 seconds, down from wave 7's 15–20 minutes) and uses the floor staff's actual locale.

## Why
By wave 13 the contract (`@invai/contracts`) is shared by four repos (backend, web, floor,
and the floor's offline outbox). Without a version handshake, a deploy that changes the
contract can make an old floor tablet silently misread or miswrite data — exactly the
kind of bug that only shows up on a real production floor, not in a dev environment where
everything redeploys together. T-13-2 through T-13-3 exist so contract drift (pieces that
used to matter but no longer do) doesn't quietly accumulate.

## What went wrong
- T-13-1 and T-13-3 both touch the contract's version number in the same window — the
  card notes explicitly that T-13-3 "rebases its bump on top" of T-13-1's commit so there's
  **one** clean version history instead of two agents racing to bump the same line.
- T-13-2's own CI check (semver-check, consumer-checkout) needed T-13-1's and T-13-3's
  contract changes to already exist before it could be tested against something real — a
  three-way sequencing dependency inside one wave, visible in the "wip" patch files left
  for T-13-4's E2E helpers before they landed cleanly.
- `team/lessons.md` doesn't log a new incident for this specific wave, which itself is
  notable: by wave 13, the git-and-migration lessons from waves 1–8 (pathspec commits,
  never `pnpm install` in a worktree, never push without being told to) had enough time
  embedded in prompts and playbooks that this wave ran without adding a new one.

## What the team learned
- A version handshake between client and server isn't just nice API hygiene — on a
  multi-repo system where one repo (floor) can be physically offline and un-updated for
  a while, it's the only thing standing between "old tablet" and "corrupted order."
- Sequencing three cards that all touch one shared version number needs an explicit plan
  (who bumps first, who rebases on top), not just three builders racing the same file —
  the same lesson wave 7 learned about shared files in general, applied here to a single
  version line that every consumer reads.

## Files to look at
- `invai-contracts/src/contract/_base.ts` (`CLIENT_TOO_OLD`), `src/compat.ts` — the version
  handshake (T-13-1).
- `invai-contracts/.github/workflows/ci.yml`, `package.json` (`check:consumers`,
  semver-check) — T-13-2.
- `invai-contracts/src/contract/*.ts`, `src/events.ts`, `src/schemas/*.ts` — the drift
  cleanup (T-13-3).
- `invai-web/e2e/`, `invai-floor/e2e/` and their `playwright.config.ts` — role/Spanish/axe
  coverage (T-13-4).
- `invai-backend/src/db/seed/builder.ts`, `src/db/seed/data.ts` — the fast, locale-aware
  seed (T-13-5).
- `invai-docs/waves/13/wip/` — the in-progress E2E helper patches before they landed.
