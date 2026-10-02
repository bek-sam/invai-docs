# Review of T-P7-4 (round 3, as wave P8 card T-P8-2)

- Reviewer: security-reviewer on Fable 5.1
- Author: platform-sre on Opus 5.5
- Verdict: approve (r2 blocking finding 1 closed; no new blocking finding; OI-23 scope kept)

## Evidence I re-ran
| Command | Result |
|---|---|
| `git archive 5add5cf team/hooks` → `/tmp/p8-2-review/new`, `5add5cf^` → `/old` (reviewed the committed copy only; the live `.claude/hooks` is being edited by T-P8-3) | both extracted; `diff -rq new/team/hooks invai-docs/team/hooks` identical |
| `python3 -B -m unittest discover -s <copy>/team/hooks/tests` with the live `settings.json` copied beside the hooks dir (3 tests read `../settings.json`; without it they error in both copies, an archive artefact, not a finding) | new: Ran 112 tests, OK; old: Ran 109 tests, OK |
| `git diff --numstat 5add5cf^ 5add5cf -- team/hooks/tests` | only `tests/test_p8_2.py` +79/−0; no existing test touched |
| `scan-test-weakening.sh invai-docs 5add5cf^` | exit 0, no hook hits |
| Own probe: 74 commands piped into old and new guard from a `/private/tmp` workspace holding `bad.sh` (`git stash`) and `ok.sh` (`ls`), verdicts diffed | 12 write forms deny→allow (the six r2 forms, both heredoc-quoting forms, `2>`, `&>`, `>|`, two redirects, `tee … > /dev/null <<EOF`); 11 write-then-run forms deny in both (`echo >; bash`, `&& ./n.sh`, `curl -o`, `cp`, `sed >`, `tee <<EOF`, heredoc-to-/tmp, `bash n.sh > out.sh`); 17 stdin-into-shell forms allow→deny (`bash < bad.sh`, abs path, `sh -s`, `zsh/fish/dash`, `sudo/env/timeout` prefixes, `--`, `-i`, `-O extglob`, `--norc`, `-o pipefail`, `>/dev/null <`, `(bash)<`, `cd d && bash < ../bad.sh`); `bash -c 'ls' < bad.sh` and `bash ok.sh < bad.sh` allow (stdin is data); 10 script runs carrying redirects still read and denied (`bash bad.sh > ./out.sh`, `./bad.sh 2>&1 \| tee`, `source … > /dev/null`, `. ./bad.sh < /dev/null`, `&>`, `>>`, `tee >(bash ./bad.sh)`, `nohup … &`); only one other verdict moved: `bash ok.sh > ./log.txt` deny→allow (the same false positive) |
| Unrelated rules, old vs new | no drift: `git stash > /dev/null` deny, `echo x > y.sh && gh repo edit` deny, `curl \| sh` deny, `bash <<< 'git stash'` deny, heredoc body with `git stash` deny (pre-existing), `docker exec … < audit.sql`, `patch -p1 <`, `pnpm test 2>&1 \| tail`, `python3 - <<EOF`, `echo ls \| bash`, docs `git status` allow |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `simple_commands` L555–565: an item whose `op` matches `REDIRECT_OP` (`>`, `>>`, `>|`, `&>`, `&>>`, `>&`, `<&`, `<>`, `<`, `<<`; `2>` lexes as `2` + `>`; `>(`/`<(` don't match the `$` anchor) skips `_script_target`; probe above |
| 2 | yes | all six forms + both heredoc-quoting forms allow in my probe and in `test_p8_2.test_writing_a_script_is_allowed` (16 subtests) |
| 3 | yes | the five named deny forms deny with "write it in one call"; 109 pre-existing tests pass unchanged |
| 4 | yes | diff is the redirect branch, `REDIRECT_OP`, one docstring sentence, one new test file; r2 notes 1–5 untouched |

## Blocking findings
none.

## Checks
- [x] Only owned paths changed (`team/hooks/guard-bash.py`, `team/hooks/tests/test_p8_2.py`, report); committed copy identical to `invai-docs/team/hooks`
- [x] Nothing outside scope (OI-23: one fix). The stdin exception (`bash < x.sh`, `sh -s < x.sh` read as a run; `-c` excluded) is judged in scope: `bash < /abs/bad.sh` was denied before r3 and dropping it would have weakened a control; feeding a file to a shell on stdin is a run of that file, so the rule's meaning is unchanged. Keep it.
- [x] Tests exercise the behavior; none weakened (109 → 112, 0 removed, scan clean)
- [x] Tenancy / idempotency / money / i18n: n/a (team tooling)
- [x] Decisions: none needed (card-local)

## Optional notes (not blocking; backlog, not a round 4)
1. Leading redirect still hides the run: `> /dev/null ./bad.sh`, `>/dev/null bash bad.sh`, `2>/dev/null ./bad.sh` allow in old and new (the first item is empty or `2`, so the words after the redirect target never reach `_script_target`). Fix later: in the redirect branch, run `_script_target(w[1:])` on the words after the target when the item is the first of its segment.
2. `bash 2>&1 < bad.sh` and `bash 0< bad.sh` deny, but by the "script 2 / 0 doesn't exist" false positive (the fd digit is lexed as the script), not by reading `bad.sh`; the author listed this. Harmless today, confusing message.
3. r2 optional notes 1–5 (`repositories/<id>`, npx writers, `$(...)` producers, realpath in `_tracked`, overwrite-then-run) remain open for the backlog per OI-23.
