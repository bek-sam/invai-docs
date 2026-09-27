# Review of T-16-3 (round 4)

- Reviewer: reviewer on claude-sonnet-5
- Author: tech-lead on claude-opus-5.5
- Verdict: changes-required

Post-approval fix on top of the already-approved round 3 (`ba99783`). Scope: `team/sync.sh`'s
`restore` step and one memory file.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-docs show e253d6c --stat` | 2 files: `team/agent-memory/qa-engineer/MEMORY.md` (+3 lines), `team/sync.sh` (1 line changed) |
| `git -C invai-docs show e253d6c -- team/sync.sh` | `cp -Rn "$B/agent-memory/." .claude/agent-memory/` → `rsync -a --ignore-existing "$B/agent-memory/" .claude/agent-memory/` |
| `bash -n team/sync.sh` | exit 0, no output |
| `which rsync && rsync --version` | `/usr/bin/rsync`, `openrsync: protocol version 29` — stock macOS tool, no new dependency |
| Scratch test outside the repo (`/tmp/rsync-test-$$`, not `sync.sh`, not the live `.claude/`): source `src/roleA/MEMORY.md` = "seed-content-A", `src/roleB/MEMORY.md` = "seed-content-B" (new), destination already has `dst/roleA/MEMORY.md` = "LIVE-EXISTING-A"; ran `rsync -a --ignore-existing "$T/src/" "$T/dst/"` | exit code **0**; `dst/roleA/MEMORY.md` still reads **"LIVE-EXISTING-A"** (untouched); `dst/roleB/MEMORY.md` now exists with "seed-content-B" (new file added); `ls "$T/dst"` shows only `roleA roleB`, no nested `src/` directory — confirms trailing-slash-on-both-sides copies *contents* into the destination, not the directory itself |
| `git status --short team/agent-memory/qa-engineer/` | **`?? golden-path-order-collision.md`, `?? stale-dev-processes.md`, `?? web-build-needs-vite-api-url.md`** — all three files the new `MEMORY.md` lines link to are untracked |
| `git log --oneline --all -- team/agent-memory/qa-engineer/{stale-dev-processes,web-build-needs-vite-api-url,golden-path-order-collision}.md` | no output — these files have never been committed, in this commit or any other |
| `git check-ignore -v team/agent-memory/qa-engineer/stale-dev-processes.md` | exit 1 — not gitignored; they should be tracked |

## What was asked: trailing-slash semantics and the never-overwrite guarantee
Both check out.
- **Trailing slash:** `"$B/agent-memory/"` (source, trailing slash) and `.claude/agent-memory/` (destination, trailing slash) is the correct rsync idiom for "copy the *contents* of this directory into that directory" — my scratch test confirms no `agent-memory/agent-memory/...` nesting occurs.
- **Never overwrite an existing live file:** `--ignore-existing` skips a destination file if it already exists, regardless of mtime — at least as strict as the old `cp -Rn`'s no-clobber behavior (arguably clearer: it's an explicit skip-if-present rule, not implicit no-clobber semantics), and my scratch test shows an existing file surviving byte-for-byte while a genuinely new file is still added.
- **The `set -e` bug is real and this fixes it:** BSD/macOS `cp -n` returns 1 when it skips a file (confirmed against `cp`'s actual behavior, matching the report); `rsync --ignore-existing` returns 0 for skips (confirmed above), so `restore` no longer aborts the script after already copying agents/skills/hooks/settings/CLAUDE.md — the install failure the tech lead described is fixed by this change specifically.

## Blocking findings
1. **`team/agent-memory/qa-engineer/MEMORY.md`'s three new lines link to files that aren't part of this commit, or any commit — they're untracked.** The commit message and the tech lead's summary both say it "adds QA's 3 merged memory lines and files," but only the lines were added; `git status` shows `stale-dev-processes.md`, `web-build-needs-vite-api-url.md` and `golden-path-order-collision.md` as untracked (`??`), and `git log --all` on those three paths returns nothing — they've never been committed. If this is pushed as-is, `main` gets a `MEMORY.md` with three dead relative links (`[Stale dev processes](stale-dev-processes.md)` etc.); a fresh clone or `sync.sh restore` on another machine would install a `MEMORY.md` pointing at files that don't exist, defeating the point of those three entries (I read all three on disk here — they're real, useful, well-formed, no PII — the content itself isn't the problem, only that it isn't tracked). Fix: `git add` the three files together with `MEMORY.md` in the same commit.

## Checks
- [x] Only owned paths touched by the tracked change (`team/sync.sh`, `team/agent-memory/qa-engineer/MEMORY.md`)
- [ ] Nothing outside scope — the untracked files are a gap in scope, not an overreach, but the commit as pushed would not match its own description
- [x] `bash -n team/sync.sh` passes
- [x] Trailing-slash and never-overwrite semantics verified by an isolated scratch test, not by inspection alone
- [x] No PII in the new memory content (read all three untracked files; process/tooling facts only)

## Optional notes (not blocking)
- The three linked files use the Claude Agent SDK's own memory-file convention (YAML frontmatter with `name`/`description`/`metadata.type`, a separate file per topic, indexed by one-line links in `MEMORY.md`) rather than the plain inline `date card: text` format the card's `verify-and-report`/`independent-review` steps specify ("one line each, starting with the date and card"). Once the files are added, it's worth a one-line decision on whether QA's richer per-topic format is fine to keep or should be flattened to match the other 12 roles' seeded style — not blocking either way, just inconsistent with the rest of this card's own convention.
