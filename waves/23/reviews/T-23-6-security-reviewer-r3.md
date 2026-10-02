# Review of T-23-6 (round 3, security co-review; T-P8-3 round 4, OI-24 answer A, S-47 only)

- Reviewer: security-reviewer on claude-fable-5-1
- Author: platform-sre on claude-opus-5-5
- Verdict: approve. Reviewed docs `b00480c` (`team/hooks/**`, report) from a `git archive` copy at `/tmp/p8-r4-sec` (removed); guard run as `tech-lead` with no stamp (`INVAI_GATE_STAMP_PATH` unset, no real stamp touched), nothing pushed, git mechanism checks in `/tmp` bare repos only, no code edited. S-46/S-48 out of scope.

## Evidence I re-ran
| Command | Result |
|---|---|
| `python3 -B -m unittest discover -s tests` on the archive; `diff -rq -x __pycache__` vs `.claude/hooks` and `invai-docs/team/hooks` | `Ran 111 tests ... OK`; identical, identical |
| Committed `test_push_stamp.py` against the `d8568aa` guard; `scan-test-weakening.sh invai-docs b00480c^` | `FAILED (failures=33)`, the deny cases prove the change; no hits (B08/B09/B10/P02 allow→deny are tightenings) |
| 57-form probe of the docs form, no stamp: URL/`upstream`/path/relative remotes, `--repo=`/`--repo`, `-o`/`--push-option`, `FETCH_HEAD:`/`HEAD:`/`carrier:`/`main:main`/`refs/heads/main`/`+main`/`:main`, two refspecs, `--`, `--force`, `$'…'`, glob, brace, `$r`, `${x:-main}`, `//` and `/.` paths, `-c remote.*` before and after `-C`, `GIT_CONFIG_GLOBAL=`/`HOME=` prefix words, `2>/dev/null`, `2>&-`, `bash -c`, fetch-from-contracts then push `$(rev-parse):main` | all deny with `PUSH_FORM_MSG`; `origin main`, `origin cafe123:main`, 40-hex `:main`, quote/backslash-equivalent spellings, `2>&1`, `2>&1 \| tail`, `; git log`, `&&`, `>/tmp/o 2>&1`, team `export PATH=…;` prefix allow |
| Author's gap `main 2 >&1`, and `… 2>&1; … push origin main 2` (borrows the first item's `>&` check) | both allow; in zsh and bash git aborts the whole push unless a local ref `2` exists (docs origin only). Low |
| Scratch bare repos: `HOME=<dir>` (and `XDG_CONFIG_HOME`) config with `[url "<code>"] pushInsteadOf = <docs url>`, then `git -C <docs> push origin main` | lands on the code remote, docs remote untouched (rc 0) |
| Guard on `export HOME=/tmp/h; <docs form>`, `HOME=/tmp/h; <docs form>`, `export XDG_CONFIG_HOME=/tmp/x; <docs form>`, `export PATH=/tmp/evil:$PATH; <docs form>`, `/tmp/evil/git -C <docs> push origin main`, zsh `function 'git' { … }; <docs form>` | all **allow**, no stamp (S-49, below) |

## Acceptance criteria (OI-24 A: a docs push is exactly `origin main` or `origin <sha>:main`)
| # | Met? | Evidence |
|---|---|---|
| S-47 | Yes | `_is_docs_push` checks `w[sub_at+1:]` as a word list against `origin` + `DOCS_PUSH_REFSPEC`; every other remote, URL, path, option and refspec denies (probe above, 33 new deny subtests); README already states the form |

## Blocking findings
none
## Checks
- [x] Only owned paths changed: `team/hooks/{guard-bash.py,tests/*}` + `waves/P8/reports/T-P8-3.md`; nothing outside scope (S-46/S-48 untouched)
- [x] Tests exercise the behavior, none weakened (scan: no hits; 33 subtests fail on `d8568aa`); tenancy, idempotency, money, en/es: n/a (hook only)
- [x] Decisions: OI-24 answer A is the decision; S-42 and S-47 set to Fixed (docs `b00480c`) and S-49 recorded in `security/v1-review.md`

## Optional notes (not blocking)
- **S-49 (Medium, new, platform-sre, due 2026-11-01):** the docs exemption tolerates any other top-level item, so the allowed `export …;` prefix redirects the exact form: `export HOME=/tmp/h; git -C <docs> push origin main` (or `XDG_CONFIG_HOME`) with a `url.<code>.pushInsteadOf` pushes to a code remote with no stamp (an allowed fetch from contracts first puts a code sha in the docs clone); `export PATH=/tmp/evil:$PATH;` or `/tmp/evil/git -C <docs> …` runs a shadow git; zsh accepts `function 'git'`, which `\bfunction\s+git\b` misses. Same class as open S-46 (any launcher), no new capability, so not blocking. Fix in `_is_docs_push`: False when any item assigns `HOME`/`XDG_CONFIG_HOME`/`PATH` (except the exact team export), when `w[0]` is not `git`/`/usr/bin/git`, widen the regex to `\bfunction\s+['"]?git\b`, require the literal `2>&1` in the raw text; add each probe to `TestDocsPush` as deny.
