# Review of T-23-6 (round 1, security co-review)

- Reviewer: security-reviewer on claude-opus-5-5
- Author: platform-sre on sonnet (card "Model")
- Verdict: changes-required

Scope of this review: the guard-hook change only (decision 0019 co-review for a security-flagged
hook edit), per the card's "Co-reviewers" line. Reviewed: `invai-infra` `3215fc6` (`scripts/gate.sh`,
`scripts/gate/lib.sh`; full diff `3dbb899..3215fc6` also inspected for stray changes — none found
outside the two gate scripts, `.gitignore`, `README.md`, `package.json`), plus the live
`.claude/hooks/guard-bash.py` (diffed against the pre-change mirror
`invai-docs/team/hooks/guard-bash.py`) and the live `.claude/hooks/tests/test_push_stamp.py`. AC1-4
(gate.sh functional behavior: real suite runs, golden-path restart, dirty-tree refusal) are the
primary reviewer's territory; I did not run the golden-path phase (instructed not to) and defer
those to the `reviewer` round. I focused on AC5/AC6 and whether the change weakens any existing
guard.

## Evidence I re-ran
| Command | Result |
|---|---|
| Existing adversarial suites (`invai-docs/team/hooks/tests/{test_guard,test_guard_segments}.py`), copied to a scratch dir with a symlinked `guard-bash.py` pointing at the live file, `python3 -B -m unittest discover` | `test_guard.py` 5/5 pass. `test_guard_segments.py` 2/3 pass; the one failure is case `B07` (`for r in invai-docs invai-backend; do git -C $r push...`), which the fixed table still expects `"allow"` — this is the *intended* new denial from round-2 finding 1's fix, not a regression. Matches the author's report exactly |
| `python3 -B -m unittest discover -s .claude/hooks/tests -p 'test_push_stamp.py' -v` (live guard, real workspace repos) | 30/30 pass (12 original + 18 new: `TestPushStampRepoResolution` x15, `TestPushStampRefspec` x3) |
| Full diff of live `guard-bash.py` vs. pre-change mirror | Purely additive: new `CWD_AMBIGUOUS`/`_advance_cwd`/`_gate_check_push`/`_push_target_dir`/`_refspec_sources`/`_gate_stamp_path`/`_find_gate_repo`, `cwd`/`git_dir_val` threaded through `simple_commands`→`git_rules`, and mechanical tuple-unpacking updates in `kill_by_pattern`/`lesson_rules` for the new 3-tuple shape. `BASH_RULES`, `PUSH_RULE`, `git_rules`'s non-push branches (`stash`, `reset --hard`, `checkout`, `switch`, `restore`, `clean`, `add`, `commit`, `config`), `kill_rules`, `kill_by_pattern`'s own logic, `PUSH_ROLES`, and `READ_ONLY_MCP` are byte-for-byte unchanged |
| Custom probe: `INVAI_GATE_STAMP_PATH=<fake fresh matching stamp for invai-backend>` as a leading command-text word, and via `export ...; git push`, subprocess env **not** carrying the var | Both `deny` (`no gate stamp for invai-backend`) — the override is read only from the guard's own process env (`os.environ`), never from the checked command text. Confirmed against `invai-backend`, which has no real stamp, to rule out a false positive from a pre-existing real stamp (see next row) |
| Custom probe: same env-var attempt against `invai-contracts` cwd | `allow` — but this is because a **real, fresh** `invai-infra/.gate/pass.json` entry for `invai-contracts` already exists on disk (written by earlier real `pnpm gate invai-contracts` runs from this review round and the primary reviewer's round 1), not because the command-text var leaked in. Verified by cross-checking against `invai-backend` (no real stamp) above |
| Custom probe: `cd invai-docs && git -C ../invai-backend push --force origin main` and the `GIT_DIR=invai-backend/.git git push --force origin main` form | Both `deny` (force-push reason) — `PUSH_RULE`/`_push_is_dangerous` are pure word/regex checks independent of the new cwd tracker, so force-push detection cannot be defeated by cwd tricks |
| Custom probe: `cd invai-docs/team && git -C ../../invai-backend push origin main`, no stamp | `deny` (`no gate stamp for invai-backend`) — multi-level relative `-C` from a tracked cwd resolves correctly |
| Independent simulation of `start_dev_all`/`stop_group` (own script, real nested `bash -c` process tree standing in for `pnpm→bash dev.sh→concurrently`, not the real dev stack, no golden path run) | `set -m` + background gives the job its own PGID; a 5-process group (parent + 2 levels of children) reaped from 5→0 processes by `stop_group`'s negative-PGID `kill -TERM`/`-KILL`. Confirms round-2 finding 3's mechanism independently of the author's own simulation |
| Manual review of `scripts/gate.sh`/`gate/lib.sh` for injection and network/secret operations | Every use of a repo name (`$repo`, `$r`) is checked against the fixed `repo_kind()` case-statement before use (`refuse` on no match); `bash -c "$cmd"` in `run_suite` only ever receives one of 6 hardcoded strings from `check_command()`'s lookup table, never attacker-influenced text. Only network/exec calls: `curl` to `localhost:3000/8000/5173/5174`, `docker exec local-postgres-1/local-valkey-1` (local containers, fixed queries, no interpolation of untrusted data), `git`/`pnpm`/`uv` on local repos. No external network egress, no secret reads or writes |

## Blocking findings

1. `.claude/hooks/guard-bash.py`, `simple_commands()` (~line 239-300, logged as S-42 in `invai-docs/security/v1-review.md`, Medium) — the cwd tracker's handling of `$(...)`/backtick command substitutions lets a push dodge the new gate-stamp check entirely, including with a `docs` cwd masking a real code-repo push. The function gathers every
`$(...)`/backtick substitution body up front via `_substitutions()`, then processes them **before**
the main `items` loop that actually advances `cwd` on `cd`/`pushd`:

```python
for body in bodies:
    result.extend(simple_commands(body, depth + 1, cwd))   # <-- cwd is still the caller's ENTRY cwd here
for idx, (words, op, here) in enumerate(items):
    ...
    if head in ("cd", "pushd"):
        cwd = _advance_cwd(w, cwd)                          # <-- cwd only advances from here on
```

Every `$(...)`/backtick body in the whole command is recursed into with the frame's *entry* `cwd`,
regardless of whether a `cd` earlier in the same command text has already moved the shell's real
working directory by the time bash would actually evaluate that substitution. This contradicts the
function's own docstring ("a … `$(...)`/backtick body gets its own copy of the *caller's*
cwd-at-that-point"): for a substitution, "at that point" is computed wrong — it's the point the
*function started*, not the point the substitution appears in the command's real execution order.
`bash -c`/`eval` bodies don't have this bug: they're handled inside the `items` loop, after `cwd`
has already advanced for any earlier `cd` in the same sequence, so `test_bash_c_cd_then_push_allows`
and friends are unaffected.

**Concrete failure scenario (reproduced against the live guard, `agent_type="tech-lead"`):**

1. `cd invai-backend && git push origin main` — correctly denied (`no gate stamp for invai-backend`).
2. The exact same push, wrapped in a command substitution: `cd invai-backend && x=$(git push origin main)` — **allowed**, no stamp required. (Also allowed with backticks, and with no outer assignment: `cd invai-backend && echo $(git push origin main)`.)
3. Worst case: session cwd is genuinely `invai-docs` (positively resolved, correctly exempt on its own). `cd ../invai-backend && git push origin main` from there is correctly **denied**. The substitution form, `cd ../invai-backend && x=$(git push origin main)`, is **allowed** — the `docs` cwd (from case 3's entry point) silently exempts a push that actually lands on `invai-backend`.

This is a real bash construct (command substitution genuinely runs in the shell's current directory
at the point it's evaluated, i.e. after the preceding `cd`), not a parser curiosity — a tech lead
piping a push's output somewhere (`x=$(git push origin main 2>&1)` to capture the output for a
report, a very natural thing to write) defeats AC5/AC6's entire purpose: an untested commit reaches
`main` with the guard's approval, no `pnpm gate` required. It does **not** weaken any *existing*
guard (force-push, tags, deploys, aws, secrets, kill-by-pattern, role-gating are all pure
regex/word checks independent of the cwd tracker, and I confirmed each still denies through a
substitution wrapper too), and it is scoped to this card's own new control, which is exactly the
class of thing I was asked to check for ("the new cwd-tracking parser can't be abused to make a
dangerous command look safe").

**Suggested fix:** don't pre-process `bodies` in a separate loop. `_substitutions()` already
replaces each body with an inline `SUBST` placeholder token in `text`/`items`, in appearance order —
interleave the recursive call for each body with the `items` loop instead, triggering it when a
`SUBST` token is encountered in an item's words (using the `cwd` value as tracked up to that item),
consuming `bodies` in order. Add regression cases to `test_push_stamp.py`
(`TestPushStampRepoResolution`) for exactly the three probes above, asserting `deny`.

## Acceptance criteria (AC5/AC6 only; AC1-4 deferred to the primary reviewer)
| # | Met? | Evidence |
|---|---|---|
| 5 | Partly | The round-1 bypass forms (`cd`, `pushd`, subshell, `bash -c`, `GIT_DIR=`, `--git-dir=`, loop/variable, `cd -`, `popd`) are now correctly resolved or fail-closed (30/30 new+existing tests, my own probes). A new bypass exists via `$(...)`/backtick substitutions (S-42), not covered by any existing test |
| 6 | Yes, but incomplete | The required 4 stamp-freshness cases plus the round-1 bypass-form regression tests exist and pass, and correctly fail on the pre-change guard (per the author's report, which I didn't re-verify against the old guard myself but whose reasoning I checked against the diff). They don't cover S-42 |

## Checks
- [x] Only owned paths changed (`.claude/hooks/guard-bash.py` push-check-only, `.claude/hooks/tests/test_push_stamp.py`, `invai-infra/scripts/gate.sh`, `scripts/gate/lib.sh` — all within the card's owned paths). `.claude/settings.json` untouched
- [x] Nothing outside scope
- [x] Tests exercise the behavior; none were weakened. The `test_guard_segments.py` `B07` mismatch is a pre-existing mirror going stale (`invai-docs/team/**` is read-only for platform-sre, already flagged by the author as blocked-by-other-owner), not a weakened test on either side
- [x] Existing guards (force-push, ref deletion, tag push, deploy, aws, secrets, kill-by-pattern, role rules) unchanged and still enforced, including under cwd tricks (verified above) — this is the "must not weaken any existing guard" requirement, and it holds
- [ ] AC5 not fully met (S-42)

## Cross-reference with the primary reviewer's round 2

`invai-docs/waves/23/reviews/T-23-6-reviewer-r2.md` (landed while I was writing this review) verdicts
`escalate` on the same `3215fc6`, with two different blocking findings in the same area: a stderr
redirect (`2>&1`) breaking a *legitimate* stamped push (their finding 1, a false positive/
availability bug — the opposite direction from S-42), and `~`/`{}` paths that don't resolve on disk
being treated as "certainly not a repo" and allowed with no stamp (their finding 2, the same false-
negative class as S-42, different vector: a non-existent literal path rather than a substitution's
stale cwd). Three independently-found bypasses in the same new mechanism, from two reviewers using
different techniques, is a signal that the cwd/path-resolution approach in `_gate_check_push`/
`_push_target_dir`/`simple_commands` needs a broader pass rather than three more point patches —
worth the tech lead's attention when deciding round 3's shape (a stricter, smaller allowlist of
resolvable forms rather than trying to enumerate every unsafe one, for example).

## Optional notes (not blocking)
- Stamp forgeability is an accepted, disclosed residual risk, not a new finding: any allowed Bash write (`printf '{...}' > invai-infra/.gate/pass.json`) or a Write/Edit to that path (not covered by `guard-paths.py`, which the card correctly left untouched) can fake a passing stamp. The card and round-1 review already call this "a speed bump, not a boundary" and explicitly out of scope for this round's blocking findings — I agree with that framing and am not blocking on it, per the task's instruction to note it as residual risk rather than fix it.
- `INVAI_GATE_STAMP_PATH` is correctly read only from the guard's own process environment (confirmed: cannot be smuggled via a leading `VAR=value` word or an `export` in the checked command text).
- No network or secret operations in `scripts/gate.sh`/`gate/lib.sh`; no injection surface via repo names or args (both are validated against fixed enums before reaching any `bash -c`/`git -C` call).
- `stop_group`'s process-group kill mechanism is sound (independently simulated, 5-process tree reaped to 0).
