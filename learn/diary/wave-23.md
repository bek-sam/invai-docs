# Wave 23 (and 23b) — P2 sweep, part 2: screens, floor, imaging, AI polish and E2E coverage

**Dates:** 2026-09-29 to 30. Wave 23b was split from wave 23 on 2026-09-29 under the
5-card cap — its cards keep their original `T-23-x` ids and live in `waves/23/`, so this
entry covers both as one wave. **Gate passed** 2026-09-30 04:51 UTC on a fresh seed (API
13/13, browser 34 passed/1 skipped, floor 3/3). **Pushed** 2026-09-30: contracts
`7ee15b6`, ui `952c174`, backend `61c6396`, web `eb1e86b`, floor `7900d0a`, imaging
`58b67ee`. Infra held back (needed S-45 and OI-22 first — resolved in wave P8).

## What was built
- **T-23-0** Backend tests never use the dev Redis DB (bug, always in scope) — the
  structural fix for wave 22's root-caused BullMQ/Redis flake.
- **T-23-6** / **T-23-7** Pre-push test gate script and GitHub Actions CI on push to main,
  E2E included (platform-sre) — the mechanical gate that later waves' pushes depend on.
- **T-23-1** Web: SCAN forms, address check, vendor resend, settings toggles, maintenance
  and QC-reason reports, buyer-photo upload, bundle split (web-engineer).
- **T-23-2** Floor: QC fail reasons, maintenance block, transfer-age warning, bin in pick
  list, camera scanner, bundle (floor-engineer) — the screens for wave 22's backend work.
- **T-23-3** Imaging polish and film-use metric; **T-23-4** AI/market polish (markdown,
  stream close, shared `ConfidenceBadge` adoption); **T-23-8** a fresh seed builds this
  week's digest; **T-23-9** two browser specs pass on a fresh seed; **T-23-10** a fresh
  seed has outside market data — the last four are all "make the gate pass on a plain,
  untouched fresh seed" fixes, not new features.

## Why
This wave closes the loop wave 22 opened: every backend capability needs a screen ("no
dead procedures"), and the test suites that prove the golden path need to actually run
mechanically on push, not rely on someone remembering to run `pnpm gate` by hand.

## What went wrong
- `pnpm i18n` (the web Spanish-string generator) turned 374 Spanish strings back into
  English and dropped 91 dynamic keys, because Spanish had been hand-edited directly into
  the generated `src/i18n/es.ts` file and never added to the JSON source files the
  generator treats as authoritative. The fix: web Spanish lives only in the i18n source
  JSONs, never hand-edited into the generated file, with a review check that the count of
  Spanish values equal to English doesn't rise.
- The push-stamp gate failed on a fresh seed **three times** for specs that earlier gates
  had only passed after someone manually forced the digest and market jobs to run first —
  the specs' real preconditions lived in comments and gate notes, not in the seed or the
  spec itself. Fixed by T-23-8/9/10, and the rule going forward: a spec passes on a plain
  fresh seed with no manual steps, or it's a bug in the seed or the spec.
- Two builders had to edit config files outside their card's listed owned paths for an
  acceptance criterion to actually work (the floor's camera permission header, the web's
  Vite chunk split) — the cards had listed only `src/**`, not the build/server config the
  AC actually needed.
- A scratch-DB reset wiped the shared dev Redis DB 0 queues (harmless here — the gate
  reseeded), and the dev CSP only allowed the API on port 3000, silently blocking a
  scratch API on another port.
- Shared `invai_test` collisions happened again: a repo check and a builder's suite ran on
  the shared test DB at the same time and one failed at suite level, because `pnpm test`
  had started truncating the shared DB at the start of every run.

## What the team learned
- A test suite's real preconditions belong in the seed or the spec itself, checked
  mechanically (`pnpm gate` now runs this) — not in a comment telling a human what manual
  step to run first.
- When writing a task card, list every config file an acceptance criterion needs (headers,
  CSP, Vite config), with a co-reviewer for any security header — not just the source
  files.
- Every agent run now pins its own `_test` database; only the gate uses the shared
  `invai_test`.

## Files to look at
- `invai-backend/src/test/` — the per-run Redis DB fix (T-23-0).
- `invai-infra/scripts/gate.sh` (or equivalent), `.github/workflows/ci.yml` — the push
  gate and CI (T-23-6/7).
- `invai-web/src/i18n/en.ts`, `es.ts`, `scripts/i18n-es.json` — the Spanish-source lesson.
- `invai-floor/src/routes/`, camera scanner permission headers — T-23-2.
- `invai-backend/src/db/seed/` — the fresh-seed market/digest fixes (T-23-8/9/10).
- `invai-docs/waves/23/wave.md` and `23b/wave.md` — full handoff notes, push SHAs, and
  team metrics.
- `invai-docs/team/lessons.md` (2026-09-30, "T-23-1 review" and "wave 23" rows).
