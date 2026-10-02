# Review of T-23-6 (round 3, as wave P8 card T-P8-3)

- Reviewer: reviewer on claude-fable-5-1
- Author: platform-sre on claude-opus-5-5
- Verdict: escalate (round 3 rule; one blocking finding, independently found and the same gap the security co-reviewer logged as S-47. Everything else in the card holds, so one small r4 fix plus its deny tests should close T-23-6)

Reviewed docs `d8568aa` (`team/hooks/**`, report) and infra `1644dd4` (`README.md`) from `git archive` copies; live `.claude/hooks` is byte-identical to the committed copy (`diff -rq -x __pycache__`, exit 0). Read-only on code; nothing pushed; stamps only via `INVAI_GATE_STAMP_PATH` in temp dirs (invai-infra HEAD / HEAD~1 SHAs); scratch dirs removed. Probe files were built from string fragments because the live guard's text rules scan the heredoc itself (`+main`, `--force`, `remote add`).

## Evidence I re-ran
| Command | Result |
|---|---|
| `python3 -B -m unittest discover -s <d8568aa copy>/team/hooks/tests` (with `.claude/settings.json` copied beside `hooks/`; without it 3 settings tests error on both old and new) | `Ran 110 tests ... OK` |
| Same on `d8568aa^` copy, and on the live `.claude/hooks/tests` | old `Ran 112 ... OK`; live `Ran 110 ... OK` |
| New `test_push_stamp.py`, `test_guard.py`, `test_guard_segments.py` against the **old** guard | `FAILED`: 78 failing subtests in 10 methods, all deny/docs/script/message cases. The deny tests prove the change |
| `scan-test-weakening.sh invai-docs d8568aa^` | `Result: no hits` |
| Own probe, 62 cases, committed guard, `tech-lead`, fresh/stale/25h/no stamp | Allowed with a fresh stamp: `git -C /Users/bekbolsun/invai/invai-infra push origin main`, `<40-hex>:main`, `<7-hex>:main`, with trailing newline or surrounding spaces, and for the main session. Denied: stale, 25h and missing stamp, `HEAD~1 sha:main`, `backend-engineer`. Denied with a fresh stamp (one message naming the form): `export PATH=...; FORM`, `FORM # c`, `true && FORM`, `FORM \|\| true`, `{ FORM; }`, `if ...; then FORM; fi`, `nohup`, `time`, backslash-newline, a tab, `bash <<'EOF'`, `source`/`.`/`bash`/`zsh`/`sh x.sh` holding the form, `--no-verify`, `--push-option`, `R=...; git -C $R push`, `cd <repo>; git push`. Existing guards in the exact form: `--force`, `-f`, `--force-with-lease`, `+main`, `--tags`, `--mirror`, `--delete`, and new `--all`/`--branches` (code and docs) all deny. Docs with no stamp: `-C <abs docs> push origin main`, `... 2>&1 \| tail -3`, after the team's `export PATH=...;`, after `cd <code repo> &&`: allow. Docs denied: `command`/`env`/`nohup`/`PATH=x` prefixes, `{ }`, `if`, `--work-tree`, `-c k=v`, `--git-dir`, `docs/./`, `docs//`, `//invai-docs`, `declare -x GIT_DIR`, `env -i GIT_DIR=x`, `D=...; git -C $D push` |
| Finding probe (no stamp, `tech-lead`) | `git -C .../invai-docs fetch /Users/bekbolsun/invai/invai-infra main` → allow; `git -C .../invai-docs push git@github.com:example/invai-infra.git FETCH_HEAD:main` → **allow**; `... push origin FETCH_HEAD:main` → allow; `... push /Users/bekbolsun/invai/invai-infra main` → allow; `... push origin main --repo=<path>` → allow |
| `grep _find_gate_repo\|_push_target_dir\|_refspec_sources\|GATE_REPO_RE` in the committed guard | no hits (folder guessing removed) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | Exact form, `main` and `<sha>:main`, any cwd, then stamp present/<24h/SHA match (probe rows 1-2, `TestOneFormStamp`) |
| 2 | Partly | Every code-repo form I tried is refused with the one message; docs `-C` form works. But a docs push is exempt whatever its remote and refspec (finding 1) |
| 3 | Yes | Force/tag/mirror/all/delete/role denies in the exact form; suites for deploy/aws/secrets unchanged (110 OK); helpers removed; diff touches only the push section, `PUSH_LONG_DENY` and the two `PUSH_CTX` lines |
| 4 | Yes | All listed cases present in `TestEveryOtherFormDenied`/`TestDocsPush`/`TestExistingPushGuards`; the 19 removed test methods are each replaced by a deny case or a stricter form (report's list checked against `comm` of method names) |
| 5 | Yes | README 57-68 and `PUSH_FORM_MSG` name the one form (seen in every deny) |

## Blocking findings
1. `team/hooks/guard-bash.py:661-678` (`_is_docs_push`) — checks `-C <DOCS_DIR>`, `GIT_*`, `--git-dir`, functions/aliases and top-level position, never `w[sub_at+1:]`, so any remote (URL, path, other name), any refspec and any push option pass with no stamp. Scenario, two commands both allowed as `tech-lead` with no stamp: `git -C /Users/bekbolsun/invai/invai-docs fetch /Users/bekbolsun/invai/invai-infra main`, then `git -C /Users/bekbolsun/invai/invai-docs push git@github.com:<org>/invai-infra.git FETCH_HEAD:main`: an un-gated infra commit lands on infra's remote `main`; `pnpm gate` never ran. The README (`1644dd4`) already promises docs is pushed only as `git -C .../invai-docs push origin main`, so the code is looser than its own doc and than OI-22 A. Fix: require `w[sub_at+1:]` to be `["origin", "main"]` (optionally `-u`/`--dry-run` and `<sha>:main`), add the fetch+URL push, `push <path> main`, `push upstream main`, `--repo=` as deny cases in `TestDocsPush`, and keep B01-B13 green. Same as S-47 (`security/v1-review.md`).

## Checks
- [x] Only owned paths changed: docs `team/hooks/{guard-bash.py,tests/3 files}` + `waves/P8/reports/T-P8-3.md`; infra `README.md` only
- [x] Nothing outside scope (`--all`/`--branches` deny is AC3's own list)
- [x] Tests exercise the behavior, none weakened: scan clean; 112→110 methods but 56×2 + 13 + 8 + 10 subtests; every removed "allows" became a deny; B07 stays deny
- [x] Tenancy, idempotency, money, en/es: not applicable (tooling)
- [x] Decisions: OI-22 answer A is the decision; nothing new needed

## Optional notes (not blocking)
- Documented residuals confirmed: `G=GIT; export ${G}_DIR=<code>/.git; <docs form>` and `export PATH=/tmp/evil:$PATH; <docs form>` allow; `python3 x.py` holding a push allows on both old and new guard (script resolution covers shells only). Fine as a speed bump once finding 1 pins `origin main`. `test_push_stamp.py` reads real `invai-contracts` commits (fails on a clone without that repo or `main~1`); old `cd -`/`popd` deny cases are now covered only by the general rule, not by name.
