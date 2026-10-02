# Review of T-23-6 (round 2, security co-review; T-P8-3 = T-23-6 round 3)

- Reviewer: security-reviewer on claude-fable-5-1
- Author: platform-sre on claude-opus-5-5
- Verdict: changes-required (S-42 is fixed; one new blocking gap in the card's own `_is_docs_push`). Reviewed docs `d8568aa` (`team/hooks/**`, report) and infra `1644dd4` (`README.md`) from a `git archive` copy at `/tmp/p8-3-sec` (removed); guard run as `tech-lead`, stamps only via `INVAI_GATE_STAMP_PATH` in a temp dir, no real stamp written, nothing pushed, no code edited.

## Evidence I re-ran
| Command | Result |
|---|---|
| `python3 -B -m unittest discover -s tests` on the archive (`../settings.json` copied beside it; without it 3 tests error on the missing file, an archive artefact) | `Ran 110 tests ... OK` |
| `diff -rq -x __pycache__` archive vs live `.claude/hooks`, and vs `invai-docs/team/hooks` | identical, identical |
| Committed `test_push_stamp.py` against the pre-change guard (`d8568aa^`) | 73 subtest failures, all deny/docs/message cases: the tests prove the change |
| `scan-test-weakening.sh invai-docs d8568aa^` | no hits |
| 113-form probe, each under a fresh matching `invai-contracts` stamp and under no stamp: the card's list plus `$(...)`, backticks, `bash -c`/`zsh -c`, `eval`, `xargs`/`-0`, `env`/`FOO=1`/`command`/`exec`/`nice`, `GIT_DIR`/`--git-dir`/`--work-tree`/`-C ... --git-dir`, `-c` config, `..`/`./`/`//`/`~`/`{}`/glob/quoted/tab/`\`-newline/uppercase, `--no-pager`, `-o`/`--push-option`, `--no-verify`, `--repo`, `HEAD:main`, `main:refs/heads/main`, two refspecs, `upstream`/URL remotes, `python -c`/`node -e`/`pnpm exec`/`npx`, `cd &&`, relative `-C`, cwd-in-repo, docs `-C -C`, docs `GIT_*`/`HOME`, docs symlink name | the 3 exact forms (`main`, 40-hex `:main`, 7-hex `:main`) allow with the stamp and deny without; every wrapper denies under both stamps with the one-form message; S-42's substitution probes deny |
| Forced/tag/mirror/delete in the exact form and for docs: `-f`, `--force`, `--force-with-lease`, `+main`, `--tags`, `v1.0.0`, `--mirror`, `--all`, `--delete`, `:main`, `-c remote.x.url=`, `-c push.default=` | all deny (`PUSH_REASON`), with and without a stamp |
| Launchers and git quirks (pre-existing, S-46) | `env -S "<form>"`, `caffeinate -i`, `stdbuf -oL`, `xcrun`, `script -q /dev/null`, `screen -dm`, `osascript -e`, `awk system()`, `expect spawn`, `$(git --exec-path)/git-push`, `git -c help.autocorrect=immediate psuh [--force]`, `${g:0:3}` all **allow** with no stamp; each launcher runs the real `git --version`; autocorrect verified `stauts`→`status` |
| Docs path to a code repo (S-47) | `git -C <DOCS> push <code-remote-url> carrier:main`, `push upstream main`, `push --repo=<url> origin main`, `push <local code repo> main:refs/heads/x`, `fetch <code repo> main:refs/heads/carrier`, `config remote.origin.pushurl <url>` all **allow**; scratch repos confirm the fetch puts the code commit in the docs clone |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | 3 exact forms allow only with a fresh stamp for that commit; stale/old/missing/other-commit deny (`TestOneFormStamp`, probe) |
| 2 | Partly | every other code-repo form denies with one message; but a docs-identified push accepts any remote and refspec (S-47), so a code commit reaches a code remote's `main` with no stamp through the docs repo |
| 3 | Yes | force/tag/mirror/all/delete/`+ref`/`:ref` deny in the exact form and for docs; `--all`/`--branches` newly denied (tightening only); `_push_target_dir`/`_find_gate_repo`/`_refspec_sources` gone |
| 4 | Yes | every required case present as a deny/allow (sub)test; 73 fail on the old guard; nothing weakened |
| 5 | Partly | README and `PUSH_FORM_MSG` state the one form; README says docs "is pushed only as `... push origin main`", which the code does not enforce (S-47) |

## Blocking findings
1. `team/hooks/guard-bash.py:661-678` `_is_docs_push` — checks `w[1:sub_at] == ["-C", DOCS_DIR]`, `GIT_*`, `--git-dir` and the top-level position, never `w[sub_at + 1:]`. Scenario, every step allowed by the committed guard as `tech-lead` with no stamp: `git -C /Users/bekbolsun/invai/invai-docs fetch /Users/bekbolsun/invai/invai-contracts main:refs/heads/carrier`, then `git -C /Users/bekbolsun/invai/invai-docs push git@github.com:<org>/invai-contracts.git carrier:main` — an un-gated contracts commit lands on contracts' `main`, `pnpm gate` never ran (also a docs exfiltration channel to any URL). Fix: require `w[sub_at + 1:] == ["origin", "main"]` (optionally `<sha>:main`), as the README already claims; add the S-47 probes to `TestDocsPush` as deny. Recorded as S-47 (Medium) in `security/v1-review.md`.

## Checks
- [x] Only owned paths changed: docs `team/hooks/**` + `waves/P8/reports/T-P8-3.md`; infra `README.md` only
- [x] Nothing outside scope (`--all`/`--branches` deny is a tightening AC3 names)
- [x] Tests exercise the behavior, none weakened (scan: no hits; 73 subtests fail on `d8568aa^`)
- [x] Tenancy, idempotency, money, en/es: n/a (hook only)
- [x] Decisions: OI-22 answer A is the decision; nothing new needed

## Optional notes (not blocking)
- S-46 (Medium, pre-existing, due 2026-10-31, platform-sre): the launcher, `git-push` binary and `help.autocorrect` bypasses above also pass the force-push guard. A launcher blocklist cannot be completed; recommend an OI for GitHub rulesets on the 7 code repos requiring the gate status, with the hook as the documented speed bump. Cheap partials are listed in the finding.
- S-48 (Low, pre-existing): `git config remote.*|url.*` writes bypass "never change remotes"; deny them like `remote set-url`.
