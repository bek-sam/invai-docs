# Review of T-20-4 (round 2)

- Reviewer: security-reviewer on Fable 5.1 (claude-fable-5-1)
- Author: platform-sre on Opus 5.5
- Verdict: **approve** (round-1 finding 1 is fixed; the fix matches the proposed rule, the six shapes deny, no lesson shape or push behavior regressed)

Inputs: the card `waves/20/T-20-4.md`, my round-1 file (`T-20-4-security-reviewer-r1.md`, finding 1: `kill_by_pattern` let a lister feed a kill through a file or a `cat` substitution), commit `f0d4b1e` in `invai-docs` (touches only `team/hooks/guard-bash.py`, `team/hooks/tests/test_guard_segments.py`, `waves/20/reports/T-20-4.md`), and the "Round 2" section of the report. Same threat model as round 1: any role's Bash call; the asset is every other agent's running API, worker and imaging process on this machine (wave-2 lesson).

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-docs show f0d4b1e` | `kill_by_pattern` lines 500–507: `LISTERS & seg_heads` still denies; then `if LISTERS & line_heads: if not pids or any("$" in p for p in pids) or not (seg_heads - {"kill"} - SHELLS) <= {"lsof"}: return True`. Identical to the rule proposed in r1 (`diff` against my r1 prototype `guard-bash-proto.py`: comments only). X12–X17 added as deny cases with the six r1 shapes verbatim. |
| `git -C invai-docs diff --stat HEAD -- team/hooks team/settings.json` | empty: the working tree equals `f0d4b1e` |
| `PYTHONDONTWRITEBYTECODE=1 uv run --no-project --with pytest python3 -B -m pytest invai-docs/team/hooks/tests -q -p no:cacheprovider` (from `invai/`) | `57 passed, 308 subtests passed in 9.82s` (was 302 in r1: +6 = X12–X17) |
| Same `test_guard_segments.py` against the **r1 guard** (`git show 9a1a445:team/hooks/guard-bash.py` swapped into a scratch copy of the hooks tree) | `6 failed, 3 passed, 66 subtests passed`: exactly X12, X13, X14, X15, X16, X17 fail with `'allow' != 'deny'`. The new tests prove the change. |
| r1 differential harness (`scratchpad/harness.py`, 96 Bash cases old vs new, 40 path cases) | Old-deny → new-allow is now **only** the six intended lesson shapes (A02, A03, A06, K01, K10, K18 = AC4). The r1 file-relay rows K03, K04, K05, K06, K15, K17 are back to `deny`. Push rows unchanged from r1 (12 shapes newly denied, 0 dangerous regressions; R08 loop tag push deny). Path cases 40/40 as expected. |
| r2 probe set (`scratchpad/r2_probes.py`, 61 cases, each stdin JSON built in the script, through old / r1 / r2 guards) | `mismatches vs expected (r2): []`. Table below. |
| `diff .claude/hooks/guard-bash.py <(git show 9a1a445~1:team/hooks/guard-bash.py)`; `test -e .claude/hooks/guard-paths.py` | live guard identical to the pre-T-20-4 copy; `guard-paths.py` not synced. **`.claude/` still untouched**, as the card requires before both approvals. |
| `bash .claude/skills/independent-review/scan-test-weakening.sh invai-docs origin/main` | hits are report and review prose plus a T-21-1 card line; no test loosened, no `.skip`, no test-only branch in hook code |
| `find invai-docs/team/hooks -name __pycache__ -o -name .pytest_cache` | none left |
| `git -C invai-docs log --oneline origin/main..HEAD` | `f0d4b1e` (this round), `9a1a445` (round 1); the other commits are wave-20/21 planning and analytics, not T-20-4 |

Stdin shape for every Bash probe: `{"tool_name":"Bash","tool_input":{"command":"<cmd>"},"session_id":"s","cwd":"/Users/bekbolsun/invai","agent_type":"<role>","agent_id":"a1"}` piped to `python3 -B <guard>`; exit 2 = deny.

### Kill rule, round-2 probes (old = pre-T-20-4, r1 = `9a1a445`, r2 = `f0d4b1e`)
| Group | Shapes | old | r1 | r2 |
|---|---|---|---|---|
| X12–X17 (r1 finding) | `pgrep -f tsx > /tmp/p; kill $(cat /tmp/p)`, newline form, `xargs kill < /tmp/p`, `ps \| grep \| awk > /tmp/p && kill $(cat …)`, `bash -c 'kill $(cat …)'`, `` kill `cat /tmp/p` `` | deny | **allow** | deny |
| New attempts on the r2 rule (20) | `kill $(< /tmp/p)`, `$(head -1 …)`, `"$(cat …)"`, `kill -- $(cat …)`, `kill -9 $(lsof -ti :3101) $(cat …)` (mixed), `xargs -a /tmp/p kill`, `pgrep \| tee /tmp/p; kill $(cat …)`, blank-line split, `sh -c "kill \$(cat …)"`, `… 2>/dev/null`, `kill -s TERM $(cat …)`, `for p in $(cat …); do kill $p; done`, `while read p; do kill $p; done < /tmp/p`, `ps -o pid= -C node > /tmp/p; kill $(cat …)`, `$(awk 1 /tmp/p)`, `eval "kill $(cat …)"`, `( kill $(cat …) )`, lister **after** the kill, `LANG=C kill …`, `/bin/kill …` | deny | allow (17) / deny (3) | **deny ×20** |
| Must stay allowed | K01–K07 from `test_guard_segments.py`; lesson shapes `pgrep -fl tsx; kill 41234`, `git push origin main; echo x \| tr -d y`, the `for r in …; do git -C $r push origin main; done; … tr -d x` loop, `git push origin main && rm -d x` (tech-lead); `pgrep -f tsx > /tmp/p; kill $(lsof -ti :3101)` (pure lsof next to a lister), `pgrep … > /tmp/p; kill 41234`, `cat /tmp/p; kill 41234; ps -p 41234`, `kill $(lsof -ti :3101)`, `kill $(cat .api.pid)` (no lister), `kill %2; ps` | mixed | allow | **allow** (all) |
| Push, no regression | `-f`, `:main`, `-d`, `--delete`, `--force-with-lease`, `+main`, chained `&&`, chained after `\| cat;`, `v1.2.3` tag, plain push as backend-engineer / reviewer → deny; plain push as tech-lead → allow | same | same | same |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Path guard | yes (unchanged since r1) | harness path cases 40/40; `f0d4b1e` doesn't touch `guard-paths.py` |
| 2 Agent known from hook input; fail-open logged | yes (unchanged since r1; tech lead kept the fail-open-with-log behavior per the report) | r1 evidence stands |
| 3 Other roles unaffected | yes | `test_other_roles_fail_open`; G31/G32 |
| 4 B-116 segment-aware push **and kill** | **yes** | push: r1 table stands; kill: X12–X17 deny, K01–K07 and `pgrep -fl tsx; kill 41234` allow, 20 further relay shapes deny (table above) |
| 5 Adversarial tests, pytest green | yes | `57 passed, 308 subtests`; X12–X17 fail on the r1 guard |

## Blocking findings
none. Round-1 finding 1 (`team/hooks/guard-bash.py` `kill_by_pattern`, Medium) is fixed and verified: every shape in the finding, plus 20 variants of the same relay, is denied; no card shape or lesson shape lost.

## Checks
- [x] Only owned paths changed: `f0d4b1e` touches `team/hooks/guard-bash.py`, `team/hooks/tests/test_guard_segments.py`, `waves/20/reports/T-20-4.md`; `.claude/**` untouched, `sync.sh` not run
- [x] Nothing outside scope: the change is the kill rule the card names in AC4; the push rule and the path guard are byte-identical to r1 in behavior (harness) and in code (diff is 10 lines inside `kill_by_pattern` plus its docstring)
- [x] Tests exercise the behavior, and none were weakened (scan hits are prose; the six new subtests fail on the r1 guard)
- [x] Tenancy / idempotency / money / en-es: n/a (hooks)
- [x] Decisions recorded where needed: none required

## Optional notes (not blocking)
1. **`lsof -c <name>` is a pattern lister the rule trusts** (both old and new allow `kill $(lsof -c node -t)` and `lsof -c node -t > /tmp/p; kill $(cat /tmp/p)`; my H01/H02). The carve-out intends `lsof -ti :<port>`. Cheap tightening in the follow-up card: treat an `lsof` word list containing `-c` (or `-u`, `-p` with a pattern) as a lister, i.e. only `lsof` with a `-i`/`:port` argument keeps the carve-out. Low; pre-existing, not introduced by this card.
2. **Two-call relay** (pre-existing, both versions): `pgrep -f tsx > /tmp/p` in one Bash call and `kill $(cat /tmp/p)` in the next are each allowed on their own (the second has no lister on the line). Closing it means denying any non-literal, non-lsof PID substitution outright (`kill $(cat …)`), which would also deny the legitimate `kill $(cat .api.pid)`. Leave as is, or allow only pid files under the workspace; a judgment call for the follow-up card with the Bash-write hole from r1 note 1.
3. r1 notes 1–7 still stand (Bash-write bypass of the path guard, `general-purpose` delegation, fork `agent_type`, push hardening for `tag <name>` / `GIT_CONFIG_*` / `git config remote.*.mirror`, the card's `python3 -m pytest` line). None changed in this round; none blocks.

Ready for the tech lead: with `reviewer`'s latest file also at `approve`, platform-sre may run `team/sync.sh` (report the diff and the `.claude/settings.json` parse check per the card), then the tech lead pushes.
