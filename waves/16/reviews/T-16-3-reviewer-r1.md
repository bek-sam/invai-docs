# Review of T-16-3 (round 1)

- Reviewer: reviewer on claude-sonnet-5
- Author: tech-lead on claude-opus-5.5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-docs show e46e2cd --stat` | 17 files: `team/agent-brief.md`, 13x `team/agent-memory/<role>/MEMORY.md`, `team/skills/independent-review/SKILL.md`, `team/skills/verify-and-report/SKILL.md`, `team/sync.sh` — all inside the card's owned paths |
| `bash -n invai-docs/team/sync.sh` | prints nothing, exit 0 — syntax OK |
| `ls /Users/bekbolsun/invai/.claude/agent-memory/*` (live state) | only empty `reviewer/` and `security-reviewer/` dirs exist, no `MEMORY.md` files yet — `restore` has not been run |
| Line-by-line diff of each seeded `## Lessons that apply to you` line against `invai-docs/team/lessons.md` (29 rows, dated 2026-09-24 to 2026-09-26, no wave-16 or wave-17 rows exist) | see Blocking finding 1 |
| `grep -n "0.x\|minor version" invai-contracts/README.md`, `cat invai-docs/decisions/0011-token-budget.md`, `cat invai-docs/decisions/0012-floor-contract-compat.md`, `grep -n B-101 invai-docs/waves/backlog.md` | the non-lessons.md facts cited below are individually true, but none is a row in `lessons.md` |
| `for f in team/agent-memory/*/MEMORY.md; do wc -l; done` | all 13 files are 12–18 lines, well under the 60-line cap |
| `awk` bullet count per file under "Lessons that apply to you" | 5–11 lines per file (`ai-engineer` and `backend-foundation` run to 11, one over the card's stated 5–10) |
| Read `team/README.md`, `team/operating-system.md` (backup/restore semantics), `wave.md` ("Nobody installs into the live `.claude/` except the tech lead, at the gate") | used for the backup/restore safety reasoning below |
| `ls invai-docs/waves/16/reports/` | empty — no `verify-and-report`-format report exists for this card (noted, not scored as a separate blocker since the task didn't ask me to require one, but it means criterion evidence rests on the diff alone) |

I did not run `sync.sh restore` (instructed not to) and did not run `sync.sh backup` (it is destructive to the very seeds under review — see finding 2).

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. `verify-and-report`/`independent-review` end with a "Save what you learned" step (0–3 entries, mistake+fix or non-obvious fact, dated, no PII, fix/delete wrong entries) | Yes | `verify-and-report/SKILL.md` new step 8, `independent-review/SKILL.md` new step 12; both match the wording required |
| 2. Agent brief has a short "Memory" section saying the same | Yes | `team/agent-brief.md` new "## Memory" section, 2 lines, matches |
| 3. Each code-building/reviewing role has a seeded `MEMORY.md`: 5–10 lessons **from `team/lessons.md`**, one line each with the lesson date, under 60 lines | Partially | All 11 build/verify roles (plus `platform-sre`, `tech-lead`) have a file under 60 lines. But see Blocking finding 1: several lines in most files are not from `lessons.md` at all, and two files (`ai-engineer`, `backend-foundation`) have 11 lesson lines, one over the stated 5–10 |
| 4. `sync.sh backup` also copies `.claude/agent-memory/` to `invai-docs/team/agent-memory/`, and `restore` copies it back | Mechanically yes, but unsafe | Both branches exist and run (see evidence above). `restore` is correctly non-destructive (`cp -Rn`, "never overwrite newer live memory" — actually never overwrites *any* existing file, a safe superset). `backup` is destructive (`rm -rf` then blind copy from live) and can permanently erase docs-side memory that live doesn't have yet — see Blocking finding 2 |

## Blocking findings
1. **`invai-docs/team/agent-memory/*/MEMORY.md` — several seeded lines are not "lessons from `team/lessons.md`" as AC3 requires, and are dated/labelled to look like they are.** `team/lessons.md` has 29 rows, all dated 2026-09-24 through 2026-09-26 and tagged with "v1 build", "Team rebuild", or "Wave 1"–"Wave 8". It has **no wave-16 or wave-17 entries at all** (wave 16 is still in progress; wave 17 is running in parallel). Yet several files contain lines like:
   - `ai-engineer:18` — `2026-09-26 W17 plan: Assistant evals have only run in mock mode (qualityPass: null); never claim quality without a real-key run.` and two more `W17 plan`/`B-101` lines — none of these exist in `lessons.md`; they read like notes pulled from wave-17 planning or the AI eval reports.
   - `architect:14` — `2026-09-25 W13: Only one card at a time holds the contracts package.json version bump and CHANGELOG entry.` — not in `lessons.md`.
   - `floor-engineer:15` — `2026-09-25 W13: Old tablets replay outbox entries after deploys; contract changes must stay compatible (ADR 0012).` — a real fact (confirmed in `decisions/0012-floor-contract-compat.md`), but not a `lessons.md` row, and mislabeled with a fabricated wave/date pairing.
   - `platform-sre:16` and `tech-lead:16` — `2026-09-26 W16: Never edit live .claude/ hooks while agents run…`, `2026-09-26 W16: Install team hooks only at the gate (sync.sh restore)…`, `2026-09-26 W16: The guard scans heredoc text too; a script quoting a blocked command gets denied.` — these describe **T-16-1/T-16-2's own in-progress, not-yet-reviewed design** (the guard hook rewrite is a sibling card under review in this same wave), presented as a settled historical lesson. If T-16-2's review changes that guard behavior, this "lesson" is wrong the moment it's seeded.
   - `security-reviewer:12` — `2026-09-26 W17: Assistant tool results are untrusted data; check new tools for cross-tenant rows and PII keys.` — not in `lessons.md`; a reasonable review heuristic, but invented, not sourced.
   - `tech-lead:13` — `2026-09-26 retro: Read each role's MEMORY.md in the retro; promote repeats to hooks.` — labelled `retro` as if a past retro produced it, but wave 16's retro hasn't happened yet (it's step 7 of the still-running wave); this is a forward-looking instruction from `operating-system.md`, not a logged lesson.
   - `web-engineer:14`, `imaging-engineer:14–15` — i18n-by-hand and imaging env/pyvips facts pulled from `agent-brief.md`/`CLAUDE.md`, not `lessons.md`, again dated as if logged.

   Failure scenario: a future ai-engineer trusts its seeded memory and treats "assistant evals have only run in mock mode" as an evergreen fact from the team's lesson log; if a later wave adds a real-key eval run, nobody has a mechanism to "fix or delete the entry that turned out wrong" (AC1's own rule) because it was never logged as a lesson in the first place — it's silently embedded as if it always was one. Likewise, the tech-lead's "guard scans heredoc text" line states T-16-2's behavior before that card's own review (round 1, same wave) has approved it; if security-reviewer's adversarial pass changes that behavior, this memory line is stale the moment `restore` installs it, with no lessons.md row to correct.

   Fix: keep only lines traceable to an actual `lessons.md` row (there are enough — 7–10 apply cleanly to every role already, e.g. `integrations-engineer`'s file is entirely `lessons.md`-sourced and meets the 5–10 range on its own). Facts from `CLAUDE.md`, `agent-brief.md`, decisions or in-flight sibling cards are legitimate things to know, but belong in a clearly separate section (not formatted as a dated "lesson"), or should wait until the fact is actually logged via `log-lesson`.

2. **`invai-docs/team/sync.sh:15-18` (`backup` branch) — destructive and asymmetric with the careful `restore` branch, and can erase this card's own seeds.** `restore` was written carefully not to clobber existing live memory (`cp -Rn`, comment "never overwrite newer live memory"). `backup` does the opposite for the exact same data: `rm -rf "$B/agent-memory" && mkdir -p "$B/agent-memory"; cp -R .claude/agent-memory/. "$B/agent-memory/"` — it deletes the **entire** `invai-docs/team/agent-memory/` tree and replaces it with whatever currently exists live, with no merge and no check for what it's about to remove.

   Failure scenario, concretely reproducible right now: live `.claude/agent-memory/` currently has only two empty role folders (`reviewer/`, `security-reviewer/` — confirmed above, no `MEMORY.md` files exist live yet, because `restore` hasn't been run since this commit). If **any** agent runs `bash invai-docs/team/sync.sh backup` before the tech lead runs `restore` at the gate — for example while saving an unrelated live edit made under a different card — it silently deletes all 13 freshly-seeded `MEMORY.md` files from the `invai-docs` working tree (recoverable only via `git checkout`/`git revert`, and only if nobody commits the backup first). This is precisely the safety property the card asked to have reasoned through: `restore`'s non-destructive design assumes `backup` won't wipe the docs side out from under it, but `backup`'s current design can. Unlike `.claude/agents/` and `.claude/skills/` (which are always fully populated live, so a full mirror is safe), `.claude/agent-memory/` is sparse and grows incrementally per role — mirroring it with `rm -rf` + blind copy is the wrong safety model for this specific subtree.

   Fix: for the `agent-memory` block only, merge instead of wipe (e.g. `cp -R .claude/agent-memory/. "$B/agent-memory/"` without the preceding `rm -rf`, or a script that only adds/updates files present live and never deletes a docs-side role folder absent live), or gate `backup`'s agent-memory step behind an explicit confirmation that `restore` has run at least once this session.

## Checks
- [x] Only owned paths changed (`git show e46e2cd --stat` — all 17 paths match the card's owned globs)
- [x] Nothing outside scope
- [ ] Tests exercise the behavior, and none were weakened — n/a, no test suite covers this shell script or these seed docs; `bash -n` is the only mechanical check available and it passes
- [x] Tenancy / idempotency / money / en-es — n/a, process/docs-only card
- [ ] Decisions recorded where needed — n/a, no cross-cutting decision required for this card

## Optional notes (not blocking)
- No report file exists at `invai-docs/waves/16/reports/T-16-3.md` (the folder is empty). The task instructions I was given didn't name a report to check, and `operating-system.md` marks the tech lead "read-only on code" with a different process than builder cards, so I'm not blocking on this — but if a report is expected for this card too, it isn't there.
- `ai-engineer/MEMORY.md` and `backend-foundation/MEMORY.md` have 11 lesson lines against the card's stated "5–10"; trimming the non-`lessons.md` lines per finding 1 would also fix this.
- The seed files' own header ("Add your own entries under 'Learned on cards': date, card, what you learned. No PII or secrets.") is good, plain, and consistent across all 13 files.
