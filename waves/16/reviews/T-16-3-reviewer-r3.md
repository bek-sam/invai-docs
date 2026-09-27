# Review of T-16-3 (round 3)

- Reviewer: reviewer on claude-sonnet-5
- Author: tech-lead on claude-opus-5.5
- Verdict: approve

Round 2 verdict was `escalate` (round-1 finding 1 was only partly fixed). The tech lead took the
escalation directly and fixed it in `f66a4477` ("T-16-3 r3"). This review verifies that fix; it is not
a third `changes-required` cycle avoiding escalation — the escalation already happened and was acted
on by its recipient.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-docs log -1 --stat` | commit `f66a4477`, "T-16-3 r3: drop the 8 seed lines not sourced from lessons.md" — 5 files, 9 deletions, no other files touched |
| `git -C invai-docs log -1 -p -- team/agent-memory/architect/MEMORY.md team/agent-memory/imaging-engineer/MEMORY.md` | confirms both the 8 round-2-flagged lines and the architect's extra `CLAUDE.md`-sourced "breaking contract change" line are removed |
| `for f in team/agent-memory/*/MEMORY.md; do count bullets; done` | 5–10 in every file (`ai-engineer` 8, `architect` 8, `backend-engineer` 10, `backend-foundation` 10, `floor-engineer` 7, `imaging-engineer` 6, `integrations-engineer` 10, `platform-sre` 8, `qa-engineer` 8, `reviewer` 7, `security-reviewer` 5, `tech-lead` 5, `web-engineer` 7) |
| `grep -h '^- ' team/agent-memory/*/MEMORY.md \| sort -u` | 26 unique lines, matching the tech lead's count |
| Cross-checked all 26 unique lines against `team/lessons.md`'s 30 rows (29 original + the Wave-16 row added in round 2), by date and source tag | every line now maps to a real row: exact quotes, accurate paraphrases of one row (e.g. the two `tsx watch` variants both come from the single v1-build row), or a reasonable per-role application of one row's rule (e.g. reviewer's "a `db/schema` diff without a migration is a blocking finding" from the Wave-7 stub row). No line references `W13`, `B-101`, `retro`, decision `0011`, or any other source outside `lessons.md`. None found unsourced. |
| `bash -n team/sync.sh` | exit 0 — unchanged since round 2 (`git diff 1c14f5d HEAD -- team/sync.sh` is empty), still the merge-based `backup` and `*.py`-only hooks copy approved in round 2 |
| Re-read every file's header (`Seeded 2026-09-26 from team/lessons.md (T-16-3); every line below is a row there.`) | now true for all 13 files, including the 5 that were false in round 2 |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1–2 (memory step in playbooks, brief section) | Yes (approved round 1, untouched since) | n/a |
| 3. Each file: 5–10 lines, all from `team/lessons.md`, one line each with the lesson date | Yes | line-count table and full cross-check above; all 26 unique lines trace to a real row |
| 4. `backup`/`restore` copy `.claude/agent-memory/` safely both ways | Yes (fixed round 2, unchanged) | `sync.sh` diff against round 2 is empty; the merge-not-wipe `backup` and non-clobbering `restore` both still in place |

## Blocking findings
None. Both round-1/round-2 findings are resolved:
1. Unsourced memory lines — all removed; every remaining line maps to a `lessons.md` row.
2. Destructive `sync.sh backup` — fixed in round 2, unchanged and re-verified here.

## Checks
- [x] Only owned paths changed (`architect`, `floor-engineer`, `imaging-engineer`, `qa-engineer`, `web-engineer` `MEMORY.md` files only)
- [x] Nothing outside scope
- [x] No test suite applies; `bash -n sync.sh` passes
- [x] No PII, secrets or customer data in any seed line (all process/tooling facts)
- [x] Decisions — n/a, no cross-cutting decision needed

## Optional notes (not blocking)
- `imaging-engineer/MEMORY.md` is now 6 lines, all generic cross-role lessons (git/pnpm/kill-PID hygiene) with nothing imaging-specific, since its two role-specific lines were the ones dropped for not being in `lessons.md`. That's correct under AC3 as written (lessons that "apply to" the role, not lessons exclusive to it), but if a real imaging-specific incident gets logged to `lessons.md` later, it'd be worth adding.
