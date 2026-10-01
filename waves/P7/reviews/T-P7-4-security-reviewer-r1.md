# Review of T-P7-4 (round 1)

- Reviewer: security-reviewer on Fable 5.1
- Author: platform-sre on Opus
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `python3 -B -m unittest discover -s <dir>/tests` for `.claude/hooks` and `invai-docs/team/hooks` | Ran 105 tests, OK (both) |
| `diff -q` live vs backup (7 `*.py` hooks + `tests/`); `diff team/settings.json .claude/settings.json` | identical; only the `PostToolUseFailure` → track-verify block added |
| 83 PreToolUse samples piped from a file into the live guard (AC1 24, AC2 13, AC3 38, AC5 8) | every card-listed deny form rc=2 (scripts, nested via abs path and `cd`, symlink, `bash <`, `cat x \| bash`, >256 KB, write-then-run incl. glob; base64/xxd/openssl/uudecode into sh/eval/source/`-s`/`<(…)`; sst secret via pnpm/npx/exec/dlx/.bin; gh api PATCH/PUT/POST/DELETE, implicit POST, `--method=`, `-H` first, GraphQL inline; gh repo edit/delete/unarchive; gh ruleset delete); every allow form rc=0 (GETs, encode, decode-to-file, kill pid, pnpm gate, heredoc commit mentioning the new verbs). `bash invai-infra/scripts/gate.sh` → ask (db:reset rule, correct for a non-QA agent) |
| 10 PostToolUse/Failure samples into track-verify.py (throwaway session, state file removed) | sed -i, perl -i on the failure event, `>`, tee, git apply after cd, cp into imaging/app recorded; docs write and same-command checks not counted |
| `scan-test-weakening.sh invai-docs origin/main` | no test hits; B07 flipped allow→deny with a T-23-6 reason (stricter, fine) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | samples above; nested scripts read when their paths resolve (a `./x` inside a script resolves against the shell cwd, as bash does) |
| 2 | yes | 13 deny / 8 allow samples |
| 3 | **no** | full-URL form bypasses the "repo itself" rule (finding 1); every path-form sample denied |
| 4 | yes | track-verify samples; `rm <repo>/src/x.ts` is not counted (note 2, not in the card's list) |
| 5 | yes | 105 green; team commands pass; one new false positive on a chained review recipe (note 1) |
| 6 | yes | docstring lists rules and limits; replacement lines in the report |

## Blocking findings
1. `.claude/hooks/guard-bash.py:478` (`setting_rules`, `ep = endpoint.split("?")[0].lstrip("/")`) — `gh api` accepts full URLs, and `GH_SETTINGS_PATH` anchors the repo-itself rule at `^repos/`. `gh api -X PATCH https://api.github.com/repos/o/r -f private=false`, the same with a trailing slash, and `gh api https://api.github.com/repos/o/r -f has_issues=false` (implicit POST) all return rc=0: an agent pasting the URL form from GitHub's docs changes repo settings with no owner approval, which is exactly the B-189 case. Sub-paths (`…/branches/main/protection` by URL) are caught only because that alternation is not anchored. Fix: strip `^https?://[^/]+/` before matching (and keep `{owner}/{repo}` placeholders working); add the three URL samples to `SecretsAndRepoSettings.test_denied`.

## Checks
- [x] Only owned paths changed (`team/hooks/**`, report; live `.claude/settings.json` wiring explained in the report; `team/settings.json` backup correctly left to the tech lead)
- [x] Nothing outside scope (post-edit-check NO_COLOR fix is a hook test repair)
- [x] Tests exercise the behavior, none weakened (B07 made stricter with reason)
- [x] Tenancy / idempotency / money / i18n: n/a (team tooling)
- [x] Decisions recorded where needed (AC4 text-based choice in the report; no cross-cutting decision needed)

## Optional notes (not blocking)
1. Written-then-run heuristic (`script_rules`, `cmd.count(name) >= 2`) false-positives on the `independent-review` step-8 recipe when the command mentions the basename again: `… && (cd $R && ./node_modules/.bin/vitest run x.test.ts)` was denied twice in this review, once with `pnpm vitest run` earlier in the chain and once with `pgrep -fl vitest` after it (`$R` is created in the same call, so the script is "missing"). Suggest triggering only when the same command also writes that name (`>`, `>>`, `tee`, `cp`/`mv` target, `chmod`), not on any second mention.
2. `shell_edits` does not count `rm <repo>/src/file` (only `git rm`); deleting a source file breaks typecheck like an edit does. Suggest adding `rm` targets.
3. Not in the card, worth a backlog row: a pipe into a shell from a non-literal producer passes (`curl … \| sh`, `echo … \| rev \| bash`); denying `\| sh|bash` unless the upstream is `echo`/`printf`/`cat <readable file>` would close the classic case. Also `gh api graphql -F query=@file` / `--input file` with a settings mutation passes (file not read; the guard already reads script files). A `*.sh`-less absolute path (`/tmp/x/evil`) is not read; the card limits AC1 to `*.sh`, fine.
4. Tech-lead question (python heredoc quoting `gh repo edit` denied): the deny comes from the pre-existing line-level regex in `BASH_RULES` (guard-bash.py:88), which has matched raw command text since wave 16; `git commit -m 'docs: mention that gh repo edit is blocked'` is denied the same way, independent of this card. The new word-level rules do not read a heredoc body as shell: `sst secret set` and `gh api -X PATCH repos/o/r` quoted in the same python heredoc are allowed. Verdict: acceptable fail-safe, pre-existing, cost is rephrasing the string. Recommended (not required): drop line 88 from `BASH_RULES` now that `setting_rules` covers the same five verbs at word level (direct, `bash -c`, scripts, and `ghedit.sh` was denied in my run), with a test that the quoted mention passes; keep line 89 (secrets, keys, dispatches), which the word rules don't cover.
