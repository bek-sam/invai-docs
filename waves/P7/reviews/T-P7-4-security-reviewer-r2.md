# Review of T-P7-4 (round 2)

- Reviewer: security-reviewer on Fable 5.1
- Author: platform-sre on Opus
- Verdict: changes-required (one new blocking finding, a round-2 regression; the r1 blocker is fixed)

## Evidence I re-ran
| Command | Result |
|---|---|
| `python3 -B -m unittest discover -s <dir>/tests` for `.claude/hooks` and `invai-docs/team/hooks` | Ran 109 tests, OK (both) |
| `diff -rq .claude/hooks invai-docs/team/hooks` | identical (only `__pycache__` in live) |
| 178 PreToolUse samples from 3 jsonl files piped into the live guard **and** the pre-r2 guard (`git archive 675d072^`), diffed: 96 gh/sst forms, 63 script/pipe/team commands, 19 write-only script creations | r1 blocker closed: every `gh api` URL form denied (host:port, userinfo, `//host`, upper-case, GHES `/api/v3//`, `?`/`#`, `--`, `--input -`, `$OWNER/$REPO`, inside `bash -c`/`eval`/`xargs`/`timeout`/`( )`, `http://`); GETs, pulls/issues writes, `gh run list`, `gh pr list` allowed. `gh repo edit|delete|rename|archive|unarchive` denied direct, `-R`/`--repo` first, `command`, `nohup … &`, `GH_TOKEN=x`, `bash -c`, `echo … \| sh`, and in a script (`bash x.sh`, `/abs/x.sh`, `./x.sh`, `source`); commit `-m`, heredoc commit, python heredoc and grep that mention them now pass. `sst secret set/remove/load` via sst/pnpm/npx denied, `sst secret list` allowed. Pipe rule: `curl \| sh`, `\| bash -s --`, `\| sudo bash`, `\| fish`, `\| xargs bash`, `pbpaste \| bash`, `cat <(curl) \| sh`, inside `bash -c` denied; `echo/printf/cat <file> \| bash`, `\| sh -c '…'`, `\| sh file`, `pnpm test \| tail` allowed |
| Team commands, old vs new | no drift: `pnpm gate` allow, `bash gate.sh` ask, backend push as tech-lead deny (gate stamp), as engineer deny, docs push allow, `kill`, `lsof`, typecheck/lint/test chains, `pnpm e2e`, `uv run`, `docker exec … < audit.sql`, review step-8 recipe with `pnpm vitest`/`pgrep vitest` allow |
| 18 PostToolUse `rm` cases → `verify-gate.py` Stop (throwaway ws under `/private/tmp`) | tracked file, abs path, `--`, glob, dir, `cd repo && rm`, `unlink`, `rm && pnpm typecheck…` block; untracked, `.bak`, `node_modules`, `$R`, `/tmp`, docs, `find -delete` don't |
| `gh api` GETs against GitHub | `/./repos/…`, `/x/../repos/…`, `repos/o/r/../r` → 404 (not real bypasses); `repositories/<id>` → resolves to the repo (note 1) |
| `scan-test-weakening.sh invai-docs origin/main` | no hook-test hits |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `bash/abs/./source` of a script with `git stash` or `gh repo edit` denied; benign script allowed |
| 2 | yes | `echo … \| base64 -d \| bash` denied with the decoder message; decode to file allowed |
| 3 | yes | all URL forms above; r1 finding 1 closed. `repositories/<id>` remains (note 1) |
| 4 | yes | `rm`/`unlink`/`git rm` of tracked paths counted (realpath caveat, note 2) |
| 5 | **no** | finding 1: write-only `*.sh` creation by path is denied (6 forms allowed before r2) |
| 6 | yes | docstring lists the new rules and the known limits (runtime-built text, aliases, node/python) |

## Blocking findings
1. `.claude/hooks/guard-bash.py` `simple_commands` (~L549 `_script_target(w)` on the item after a redirect) + `_written_here` (~L1026 redirect branch) — the redirect target `> /path/x.sh` is parsed as a simple command whose head is an absolute or slash path ending in `.sh`, so it becomes a SCRIPT_REF; the file is missing and the same segment "writes" it, so the new rule denies. Nothing runs the file. Denied today (all allowed by the pre-r2 guard): `echo 'ls' > /tmp/p74r2/w1.sh`, `cat > /tmp/p74r2/w2.sh <<'EOF' … EOF`, `echo ls > ./w8.sh`, `mkdir -p scripts && cat > scripts/w6.sh <<EOF`, `cat > invai-infra/scripts/new.sh <<EOF` (platform-sre's own flow), `echo … > /tmp/x.sh; echo written`. `tee`, `cp`, `curl -o`, `mv` and a slash-less `> w7.sh` still pass. Scenario: an agent follows the guard's own deny message ("write it in one call and run it in the next") with a heredoc and is denied on the write call with a message about a script it never ran; the two-step flow the control prescribes is impossible for the most common write form. Fix: a word that follows a redirect op (`>`, `>>`, `>|`, `&>`, `<`) is a file, not a command: skip `_script_target` for that item (or drop refs whose only "run" segment is the redirect). The deny cases (`echo … > n.sh; bash n.sh`, `curl -o`, `cp`, `sed > …; bash`) keep their real run segment and stay denied; add the six forms above as allow tests.
## Checks
- [x] Only owned paths changed (`team/hooks/**`, report); live copies identical
- [x] Nothing outside scope; no weakened tests (new tests only add cases)
- [x] Tenancy / idempotency / money / i18n: n/a (team tooling)

## Optional notes (not blocking)
1. `GH_SETTINGS_PATH` anchors the repo-itself rule at `^repos/`; GitHub also serves the repo at `repositories/<id>` (verified with a GET), so `gh api -X PATCH repositories/12345 -f private=false` passes. Add `|^repositories/\d+/?$`.
2. `invai_hooklib._tracked` returns False on any non-zero git exit (the report says a git error counts it); `full` is not realpath'd while `find_repo` is, so under a symlinked cwd (`/tmp` → `/private/tmp`) `relpath` crosses roots, git errors, and the `rm` is not counted (my probe needed `/private/tmp` to pass). Workspace paths are not symlinked today. Realpath `full`; count when stderr is not "did not match".
3. `NAME_READERS` lists `npx`, `pnpm`, `pnpx`, `yarn`, `bunx` wholesale: `npx -y cpy-cli /tmp/bad.sh n.sh; bash n.sh` now passes (pre-r2 denied). Treat `npx`/`pnpx`/`bunx`/`pnpm exec|dlx`/`yarn dlx` as writers; keep `pnpm vitest|run|test`.
4. Pipe rule: a literal producer with a substitution passes: `echo "$(curl -s …)" | sh`, `printf '%s' "$(cat bad.sh)" | bash` (the cat-reading in `cat bad.sh | bash` is sidestepped). Deny when the echo/printf/cat words contain `$(`, a backtick or `<(`; `$VAR` is already a listed limit.
5. Pre-existing, backlog: overwrite-then-run reads the old content (`cp bad.sh exist.sh; bash exist.sh`, `printf … > exist.sh; bash exist.sh`); glob-copy then run (`cp /tmp/ba* d/; bash d/bad.sh`). Bash-expansion evasions (`$'repos/o/r'`, `repo{s,}/o/r`, `${X:-…}`, `$(which gh) repo edit`) pass, consistent with the denylist-for-mistakes scope.
