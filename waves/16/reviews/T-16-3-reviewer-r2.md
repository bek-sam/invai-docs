# Review of T-16-3 (round 2)

- Reviewer: reviewer on claude-sonnet-5
- Author: tech-lead on claude-opus-5.5
- Verdict: escalate

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-docs show 1c14f5d --stat` | 15 files: 13x `team/agent-memory/<role>/MEMORY.md`, `team/lessons.md`, `team/sync.sh` — all inside owned paths |
| `bash -n invai-docs/team/sync.sh` | exit 0, no output — syntax OK |
| `cat invai-docs/team/sync.sh` (full, both branches) | `backup`'s agent-memory step no longer does `rm -rf`; it's `mkdir -p` + `cp -R` only (merge, not wipe). `restore` still uses `cp -Rn` (unchanged, still correct) |
| `ls -la /Users/bekbolsun/invai/.claude/hooks/` | live has only `guard-bash.py`; confirms `backup`'s old `cp "$B"/hooks/* .claude/hooks/` (no `-R`) would have hit a directory once `tests/` exists and aborted under `set -e` — the self-reported bug is real and plausible |
| Diff of every `## Lessons that apply to you` bullet, all 13 files, against `team/lessons.md`'s 29(+1) rows | see Blocking finding 1 — 8 lines across 5 files still don't match any row |
| `grep -n "W13\|B-101\|retro\|W16\|W17" team/lessons.md` | only false-positive matches (the word "retro" inside "promote to X at retro" in the Enforced-in column); confirms `lessons.md` still has no W13, W16 (other than the one new row), W17 or B-101 sourced rows |
| `for f in team/agent-memory/*/MEMORY.md; do count bullets; done` | all 13 files now 5–10 lines (previously `ai-engineer` and `backend-foundation` were 11) |
| `git -C invai-docs show 1c14f5d -- team/lessons.md` | one new row added, Wave 16, guard-vs-heredoc incident, backing the tech-lead's own remaining `2026-09-26 W16` line — correctly sourced now |

I did not run `sync.sh` (backup or restore), per instruction.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1–2 (memory step in playbooks, brief section) | Yes (unchanged from r1, already approved) | not re-touched in this diff |
| 3. Each file: 5–10 lines, all from `team/lessons.md`, one line each with the lesson date | Partially | Line-count range is now correct everywhere. But 8 of the remaining lines, across 5 files, are still not rows in `lessons.md` — see Blocking finding 1. The per-file header was also changed to assert *"every line below is a row there"*, which is now a false claim in those 5 files |
| 4. `backup` also copies `.claude/agent-memory/` to the docs copy; `restore` copies it back, safely | Yes | `backup`'s agent-memory step is now a merge (`cp -R` with no preceding `rm -rf`) — round-1 finding 2 is fixed. Verified by reading the script; a live-only file is left alone, a live file with the same name overwrites its backup copy, and a backup-only file (e.g. an unrestored seed) survives, exactly as the new comment states |

## Blocking findings
1. **Round-1 finding 1 is only partly fixed: 8 lines across 5 files are still not rows in `team/lessons.md`, and the updated header now falsely claims they all are.** The wave-16/17/`B-101`/`retro`-tagged lines from round 1 were correctly removed. But these remain, unchanged from round 1, and still have no matching row in `lessons.md` (which has no `W13` entries and no rows for imaging/i18n/seed-runbook facts):
   - `team/agent-memory/architect/MEMORY.md:14` — `2026-09-25 W13: Only one card at a time holds the contracts package.json version bump and CHANGELOG entry.`
   - `team/agent-memory/floor-engineer/MEMORY.md:14` — `2026-09-25: Add en and es UI text by hand; never run pnpm i18n.` and `:15` — `2026-09-25 W13: Old tablets replay outbox entries after deploys; contract changes must stay compatible (ADR 0012).`
   - `team/agent-memory/imaging-engineer/MEMORY.md:13-14` — the pyvips/peak-RSS line and the `IMAGING_SHARED_SECRET` line (both facts from `CLAUDE.md`/the imaging README, not `lessons.md`).
   - `team/agent-memory/web-engineer/MEMORY.md:14` — the same i18n-by-hand line, and `:15` — `2026-09-25 0011: At most 6 screenshots per card...` (sourced from decision `0011`, not `lessons.md`).
   - `team/agent-memory/qa-engineer/MEMORY.md:14` — `2026-09-26: Seed with imaging up and the worker stopped...` (from `agent-brief.md`, not `lessons.md`).

   Every one of these five files' header was changed in this same commit to read *"Seeded 2026-09-26 from `team/lessons.md` (T-16-3); every line below is a row there."* That sentence is now factually wrong for all five files — it was true of neither round, but round 1 didn't claim it. Failure scenario: an architect trusts the header, assumes the W13 line is a logged, correctable lesson, and never checks `lessons.md` for it — but `log-lesson`'s own "fix or delete an entry that turned out wrong" mechanism only works on rows that exist in `lessons.md`; this one doesn't, so a wrong fact here has no correction path.

   This is the same category of finding as round-1 finding 1 (not a new issue introduced by the fix), so per the review policy this round is `escalate`, not a second `changes-required`.

## Checks
- [x] Only owned paths changed (`git show 1c14f5d --stat` matches the card's owned globs; `team/lessons.md` append is explicitly any-role-editable per `operating-system.md`)
- [x] Nothing outside scope
- [ ] n/a — no test suite covers these files; `bash -n` is the only mechanical check available and passes
- [x] Round-1 finding 2 (destructive `backup`) is fixed and verified by reading the script
- [ ] Round-1 finding 1 (unsourced, mislabeled lesson lines) is only partly fixed — see above

## Optional notes (not blocking)
- `backup`'s hooks step is also no longer a full mirror (`rm -rf` removed, now merges `*.py` files by name). This protects `tests/` as intended, but means a hook script removed from live will now linger in the docs copy forever unless removed by hand — the same "remove stale entries by hand" caveat the memory comment already states, just not written down for hooks. Low severity; worth a one-line comment if there's a round 3.
- The new `lessons.md` row (Wave 16, guard hook vs. heredoc text) reads as a plausible, specific incident and is correctly the source for the tech-lead's own remaining memory line — good pattern to repeat for the other 8 lines above instead of removing them outright.
