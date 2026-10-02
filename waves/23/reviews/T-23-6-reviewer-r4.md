# Review of T-23-6 (round 4, as wave P8 card T-P8-3; OI-24 answer A, limited to S-47)

- Reviewer: reviewer on claude-fable-5-1
- Author: platform-sre on claude-opus-5-5
- Verdict: approve

Reviewed docs `b00480c` from a `git archive` copy (`/tmp/p8-r4-rev`, removed after); live `.claude/hooks` is byte-identical to `invai-docs/team/hooks` (`diff -rq -x __pycache__`, exit 0) and the worktree guard matches the commit. Read-only on code; nothing pushed; stamps only via `INVAI_GATE_STAMP_PATH` in the scratch dir (infra `main` / `main~1` SHAs). Infra `README.md` unchanged since `1644dd4` (lines 11-12 already state the docs form).

## Evidence I re-ran
| Command | Result |
|---|---|
| `python3 -B -m unittest discover -s <b00480c copy>/team/hooks/tests` (settings.json copied beside `hooks/`) | `Ran 111 tests ... OK` |
| Same on the `b00480c^` copy | `Ran 110 tests ... OK` |
| New `test_push_stamp.py` against the **old** guard | `FAILED (failures=33)`, all in `test_docs_push_other_words_denied`; new `test_guard*.py` on old guard: 4 failures = P02, B08, B09, B10 (the fix is proven) |
| `scan-test-weakening.sh invai-docs b00480c^` | `Result: no hits` |
| Own PreToolUse probe, 43 rows, committed guard, `tech-lead` unless noted | 0 mismatches. Denied with no stamp: URL push `FETCH_HEAD:main`, `fetch <infra> main; push <url> FETCH_HEAD:main` (the r3 scenario), `origin FETCH_HEAD:main`, `push <abs infra path> main`, `--repo=` after and `--repo <url>` before, `upstream main`, `main:main`, two refspecs, `$REF`, `-C docs -C ../invai-infra`, `2>/tmp/x`, `1>&2`, `2>&1 --repo=`, uppercase sha, `-4`, `-q`, quoted extra word, `2 >&1 \| <second push>`, `--mirror`, `--delete`. Allowed with no stamp: `push origin main`, `docs/` trailing slash, 7- and 40-hex `:main`, `2>&1`, `2>&1 \| tail -3`, `; git log`, after `export PATH=...;`, quoted `"main"`. Code form unchanged: infra `push origin main`/`<sha>:main`/`<7-hex>:main` allow with a fresh stamp; stale 25 h, no stamp, SHA mismatch, `2>&1 \| tail`, `export PATH=x;` prefix, `backend-engineer`, `--tags`, `--all` all deny |
| Same probe on the old guard | the 8 S-47 rows allow (bypass confirmed present before, closed now) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | `CODE_PUSH_FORM` untouched in the diff; code-form probe rows above |
| 2 | Yes | r3 finding 1 / S-47 closed: `_is_docs_push` now requires `w[sub_at+1:]` == `origin main\|<7-40 hex>:main`; every other remote, path, option or refspec falls to the code rule and `PUSH_FORM_MSG` (seen in the deny output) |
| 3 | Yes | Force/tag/mirror/all/delete rows deny; diff is 16 lines in `_is_docs_push` + regex + message, nothing else in the guard |
| 4 | Yes | The four allow→deny changes (P02 bare push, B08 `-u`, B09 `--dry-run`, B10 `HEAD:main`) are exactly what OI-24 A rules out; the two removed allows in `test_docs_push_allowed_without_stamp` reappear in the deny list; 33 new deny subtests fail on the old guard |
| 5 | Yes | `PUSH_FORM_MSG` now names both docs forms; README 11-12 consistent |

## Blocking findings
none

## Checks
- [x] Only owned paths changed: `team/hooks/{guard-bash.py,tests/test_guard.py,tests/test_guard_segments.py,tests/test_push_stamp.py}` + `waves/P8/reports/T-P8-3.md` (5 files, +68/-8)
- [x] Nothing outside scope (S-47 only; S-46/S-48 untouched as OI-24 says)
- [x] Tests exercise the behavior, none weakened: scan clean; 110→111 methods; every expectation change is allow→deny
- [x] Tenancy, idempotency, money, en/es: not applicable (tooling)
- [x] Decisions: OI-24 A is the decision; nothing new needed

## Optional notes (not blocking)
- Author's gap confirmed: `git -C <docs> push origin main 2 >&1` allows. It is a docs-origin push of refspecs `main` and `2`; no ref named `2` exists in docs (`for-each-ref`), so git fails with "src refspec 2 does not match any" and pushes nothing; with such a ref it would push only to docs' own origin. Not a code-repo gate bypass; fine to leave logged.
- `test_push_stamp.py` still depends on the real `invai-contracts` repo having `main~1` (as noted in r3).
