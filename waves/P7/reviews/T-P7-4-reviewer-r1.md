# Review of T-P7-4 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: platform-sre on Opus
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `python3 -B -m unittest discover -s .claude/hooks/tests` | Ran 109 tests OK |
| `python3 -B -m unittest discover -s invai-docs/team/hooks/tests` | Ran 109 tests OK |
| `diff -q` each live `.claude/hooks/*.py` vs `invai-docs/team/hooks/*.py`, and `diff -rq` the two `tests/` dirs | no differences |
| `diff .claude/settings.json invai-docs/team/settings.json` | only the live file has the new `PostToolUseFailure` → `track-verify.py` (Bash matcher) block, as the report says; `team/settings.json` is outside the card's grant, correctly left for the tech lead |
| 35 adversarial PreToolUse JSON samples piped to the installed `guard-bash.py` via a wrapper script (not inline, to avoid tripping the guard on myself) | 0 mismatches. Deny confirmed: `sst secret set`, `gh api -X PATCH https://api.github.com/repos/o/r` (full URL, the round-1 security finding), `gh api -X DELETE .../collaborators/bob` (full URL), `gh api repos/o/r/branches/main/protection -X POST`, `gh repo edit`, `gh ruleset delete`, `curl\|sh`, `wget -O-\|bash`, `echo\|rev\|bash`, `printf...\|tee x.sh\|bash`, base64-decode-then-bash/eval, write-then-run via `>`, `;`, `&&`, with an `ls` reader interposed, and via `cp` of another file onto the `.sh` target. Allow confirmed: GETs, `gh ruleset list`, a commit message mentioning "gh repo edit", a heredoc commit body mentioning "gh repo delete", `kill <pid>`, `bash invai-infra/scripts/dev.sh`, the exact `pnpm vitest`/`pgrep -fl vitest`/`cp vitest.config.ts`/`(cd $R && ./node_modules/.bin/vitest …)` recipe the security-reviewer flagged as a false positive in round 1 (now allowed), and the here-string regression probe `sh <<< 'git push -f origin main'` (wave-16 canary gap) still denies |
| `python3` probe of `invai_hooklib.shell_edits()` against a throwaway git repo | `rm <tracked file>` → counted as an edit; `rm <untracked file>` → not counted; `git rm` → still counted (round-2 fix (b) confirmed) |
| `gh api graphql -F query=@file` with a settings mutation in the file | allow (documented known gap, not an AC; security-reviewer's note 3, non-blocking) |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-docs 74d0058^` | `test_p7_4.py`: 0 assertions removed, 32 added; no `.skip`/`.only`, no loosened config, no snapshot changes; the one "test-only branch" hit is a literal set of directory-name strings (`SKIP_PARTS`) matching the scanner's text pattern, not a real branch — known false-positive class |
| `git show --stat` on 74d0058, 8cd5f18, 675d072 | touch only `team/hooks/**` and `waves/P7/reports/T-P7-4.md`; matches owned paths |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 (scripts read) | yes | write-then-run denies hold under `;`/`&&`/interposed `ls`/`cp` (my probes); 109 green covers nested/binary/>256KB/missing cases |
| 2 (encoded commands) | yes | base64/xxd/openssl/eval probes above all deny; plain decode-to-file allows |
| 3 (B-189 secrets/repo settings) | yes | path-form and full-URL-form `gh api` writes deny (round-1 finding fixed and independently re-verified); `sst secret`, `gh repo edit`, `gh ruleset delete` deny; GETs and `gh ruleset list` allow |
| 4 (shell edits count) | yes | `rm`-tracked-file probe confirms round-2 fix (b); report's test list (18 write forms, 11 non-writes, failure event, same-command exclusion, bystander-agent exclusion) matches the diff I read |
| 5 (no regressions) | yes | 109/109 both copies; B07 push-stamp row change matches the pre-existing T-23-6 ambiguous-`cd $r` rule (`_push_target_dir`/CWD_AMBIGUOUS), stricter not weaker |
| 6 (docs) | yes | live docstring (read in full) matches the behavior I probed and the replacement lines given to the tech lead |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`team/hooks/**`, `waves/P7/reports/T-P7-4.md`; `.claude/hooks/**` is not a git repo per the card, verified identical to the backup)
- [x] Nothing outside scope (the `post-edit-check.py` NO_COLOR fix is a hook-test repair inside owned paths, not new scope)
- [x] Tests exercise the behavior, none weakened (scan: 0 removed/32 added assertions; B07 flip is a correctness fix tied to a prior wave's rule, with a reason comment)
- [x] Tenancy / idempotency / money / i18n: n/a (team tooling, no app code or tables touched)
- [x] Decisions recorded where needed: n/a for a decisions/ entry; the AC4 text-vs-fingerprint choice and its cost are stated in the report

## Optional notes (not blocking)
- Report is 77 lines (card budget is ≤60); the overage is round-2's fix log, which is useful content. Not a correctness issue.
- `gh api graphql -F query=@file` / `--input file` with a settings mutation still isn't read (security-reviewer's note 3). Already named as a known gap in the report; worth a backlog row if not already filed.
