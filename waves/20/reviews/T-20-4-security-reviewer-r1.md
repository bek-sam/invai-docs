# Review of T-20-4 (round 1)

- Reviewer: security-reviewer on Fable 5.1 (claude-fable-5-1)
- Author: platform-sre on Opus 5.5
- Verdict: **changes-required** (one Medium blocking finding on the kill rule; the push rule and the path guard are sound)

Inputs: the card `waves/20/T-20-4.md`, commit `9a1a445` in `invai-docs` (no later T-20-4 commits touch `team/hooks` or `team/settings.json`: `git log --oneline -- team/hooks team/settings.json`), and the report `waves/20/reports/T-20-4.md`. Threat model: the caller is a `tech-lead` or `reviewer` subagent (or any role for the kill rule) running Bash or a file tool; the assets are the pushed history of the 8 repos (force-push and ref deletion are irreversible; tags deploy), other agents' running processes, and product code the tech lead and reviewer must not edit. Worst outcome for a bypass: a rewritten `main` or a tag push that deploys.

## Evidence I re-ran
| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 uv run --no-project --with pytest python3 -B -m pytest invai-docs/team/hooks/tests -q -p no:cacheprovider` (from `invai/`) | `57 passed, 302 subtests passed in 9.03s` |
| `python3 -m pytest --version` (system 3.13.5) | `No module named pytest` (the card's literal command doesn't run on this machine; the uv form above is the equivalent, matches the author's note) |
| `ls .claude/hooks; test -e .claude/hooks/guard-paths.py` | 6 files dated Sep 27, `guard-paths.py` absent |
| `diff .claude/hooks/guard-bash.py <(git -C invai-docs show 9a1a445~1:team/hooks/guard-bash.py)` | identical: the live guard is the pre-T-20-4 copy; the other 5 live hooks equal their team copies; `.claude/settings.json` differs from `team/settings.json` only by the new `guard-paths.py` entry (not synced). **`.claude/` untouched, as required.** |
| New tests against the OLD guard (`test_guard_segments.py` with `GUARD` pointed at `git show 9a1a445~1:team/hooks/guard-bash.py`) | 10 subtests FAIL on the old code (B01, B02, B03, B05, B07, B11, B12, B13, D16, D17): the tests prove the change |
| `bash .claude/skills/independent-review/scan-test-weakening.sh invai-docs origin/main` | hits are report prose only (`waves/20/reports/T-20-4.md`); no config loosened, no test-only branches in hook code |
| My differential harness: 96 Bash cases through old and new `guard-bash.py`, 40 stdin cases through `guard-paths.py` (`/private/tmp/claude-501/-Users-bekbolsun-invai/665251eb-61e3-4073-8cb8-b8559efc8fa8/scratchpad/harness.py`; reproduce with the JSON shapes below) | push: 0 dangerous regressions, 12 shapes newly denied; kill: **6 shapes previously denied are now allowed (finding 1)**; paths: 40/40 as expected |
| `find invai-docs/team/hooks -name __pycache__ -o -name .pytest_cache` | none left |
| `git -C invai-docs diff --stat origin/main -- team/hooks team/settings.json` | only `team/hooks/guard-bash.py`, `team/hooks/guard-paths.py`, `team/hooks/tests/test_guard_paths.py`, `team/hooks/tests/test_guard_segments.py`, `team/settings.json` (+ the report): inside the card's owned paths |

Stdin case shape used for every Bash probe (agent as noted): `{"tool_name":"Bash","tool_input":{"command":"<cmd>"},"session_id":"s","cwd":"/Users/bekbolsun/invai","agent_type":"<role>","agent_id":"a1"}` piped to `python3 -B invai-docs/team/hooks/guard-bash.py`; exit 2 = deny. Path probes: `{"hook_event_name":"PreToolUse","tool_name":"Write","cwd":"...","tool_input":{"file_path":"<path>","content":"SECRET"},"agent_type":"<role>"}` with `CLAUDE_PROJECT_DIR=/Users/bekbolsun/invai` and `INVAI_GUARD_PATHS_LOG` pointed at my scratchpad.

### Push rule: bypass attempts (all denied by the new guard; `old` = pre-T-20-4)
| Shape | old | new |
|---|---|---|
| `git -c alias.p=push p origin +main`, `git -calias.x=push x -f`, `git config alias.p 'push -f' && git p` | deny | deny |
| `GIT_TRACE=1 git push -f …`, `env … git push --force …`, `command git push -f …`, `/usr/bin/git push origin +main`, `\git push -f …`, `g""it pu''sh -f …` | deny | deny |
| `git${IFS}push${IFS}-f${IFS}origin${IFS}main` | **allow** | deny |
| `bash -c "git push -f …"`, `sh -c 'bash -c "git push --delete …"'`, `echo 'git push -f …' \| sh`, `printf … \| bash -s`, `eval 'git push --force …'`, `echo origin \| xargs git push -f`, `( … )`, `{ …; }`, newline, `\`-continuation, heredoc, here-string, `find -exec`, `timeout 30 git push -f` | deny | deny |
| `python3 -c "subprocess.run(['git','push','-f',…])"` | **allow** | deny |
| `git push origin main $'-f'`, `F=-f; git push origin main $F`, `${F}`, `"$F"`, `set -- --force; … "$@"` | **allow** | deny |
| `git push -4f …`, `--del`, `--mir`, `--prune`, `main:+main`, `-c remote.origin.mirror=true`, `-c push.followTags=true`, `git send-pack --force` | **allow** | deny |
| `git -C dir push -f`, `--git-dir=… push -f`, `--git-dir … push +main`, tab before `-f`, `-o x -f`, `--force-if-includes`, `:refs/heads/main`, `'+main'`, `--tags`, `tag v1.2.3`, `origin main -d`, `\|& cat`, unbalanced-quote fallback | deny | deny |
| Role rule: reviewer `git push origin main`; backend-engineer `echo x; git push origin main` | deny | deny |
| Lesson shapes now allowed for tech-lead: `git push origin main; echo x \| tr -d y`, the `for r in …; do git -C $r push origin main; done; … tr -d x` loop, `git push origin main && rm -d x` | deny | allow (intended, AC4) |

Not caught by either version (no regression; hardening notes below): `git push origin tag release-2026`, a bare tag name without `v` (`git push origin release-2026-09-28`), `GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=remote.origin.mirror … git push origin`, `git config remote.origin.mirror true; git push origin`, base64-to-shell (documented out of reach).

### Path guard (40 cases)
Denied for tech-lead: `invai-backend/src/auth.ts` (Write and Edit), `.claude/hooks/guard-bash.py`, `.claude/settings.json`, `.claude/settings.local.json`, `waves/20/reviews/*` (direct and via `reports/../reviews/`), `invai-docs/security/v1-review.md`, `product/scope.md`, `../invai-web/src/x.tsx` from cwd `invai-docs`, a non-existent leaf under `waves/20/newdir/../../../../invai-backend/`, `NotebookEdit` of `invai-backend/n.ipynb`, `plugin:tech-lead` name form, `.claude/agent-memory/security-reviewer/`, `~/…`, `/etc/hosts`, my scratchpad, `invai-backend/CLAUDE.md`, the `waves` dir itself. Allowed: waves/team/skills/agents/memory paths, relative `waves/20/wave.md` from cwd `invai-docs`, case variants. Reviewer: only `waves/<n>/reviews/**` (incl. subfolders) and `.claude/agent-memory/reviewer/**`; card, report, backend, `waves/reviews/` at the wrong depth, `invai-docs/.claude/agent-memory/reviewer/` all denied. Main session (no `agent_type`), `security-reviewer`, `general-purpose`: allowed. No case crashed; every restricted-role failure path (no path, no workspace, bad JSON, bad `cwd`) is a deny; other roles pass (`test_other_roles_fail_open`). Malformed JSON denies for everyone, same as `guard-bash.py` today: Claude Code always sends JSON, so this is not a crash-deny risk in practice.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Path guard (tech-lead and reviewer trees, message names paths and "write a card for the owner") | yes | table cases T01–T40, R01–R18, `test_denial_names_paths_and_says_write_a_card`; my 40 probes above |
| 2 Agent known from hook input; missing type → allow + one log line (time, caller, tool, path; no content) | yes, with one open question | `test_main_session_allowed_and_logged_without_content`, `test_subagent_without_type_allowed_and_logged`; `team/state/.gitignore` (`*`) already existed. Source recorded in the report (headless probe on 2.1.283). Open: what `agent_type` a **fork** of the tech lead reports (see note 3) |
| 3 Other roles unaffected | yes | O01, O02, O05; my G31/G32 |
| 4 B-116 segment-aware push and kill | **push yes; kill partially** | push: all card shapes and 35 chained/nested variants denied, lesson shapes allowed. Kill: literal-PID + listing allowed, but the segment split lets a lister feed a kill through a file (finding 1) |
| 5 Adversarial tests, pytest green | yes | 57 passed, 302 subtests; the new segment tests fail on the old guard |

## Blocking findings
1. **`team/hooks/guard-bash.py:487-502` (`kill_by_pattern`) — Medium (integrity of a team control; a previously denied command is now allowed).** The cross-segment check only fires when a kill's PID word contains `$`. A lister's output relayed through a file or a substitution that isn't a `$var` is not seen, so these were **denied by the old guard and are allowed now** (all as `backend-engineer`):
   - `pgrep -f tsx > /tmp/p; kill $(cat /tmp/p)`
   - `pgrep -f tsx > /tmp/p\nkill $(cat /tmp/p)`
   - `pgrep -f tsx > /tmp/p; xargs kill < /tmp/p`
   - `ps aux | grep '[t]sx' | awk '{print $2}' > /tmp/p && kill $(cat /tmp/p)`
   - `pgrep node > /tmp/p; bash -c 'kill $(cat /tmp/p)'`
   - ``pidof node > /tmp/p; kill `cat /tmp/p` ``
   Failure scenario: an agent cleaning up "its" tsx watchers writes `pgrep -f tsx > /tmp/p; kill $(cat /tmp/p)` and kills every other agent's API and worker on the machine, the exact wave-2 lesson this rule exists for. This is a kill by process pattern in two segments, not a determined base64-style bypass.
   **Fix that keeps every card shape (prototyped in my scratchpad, author's full suite `test_guard.py` + `test_guard_segments.py` still OK, all six shapes above denied, K01/K04/K06/K07 and the lesson shapes still allowed):** when a lister appears anywhere on the line and the kill's PIDs are not all literal, deny unless the kill's own segment is a pure port lookup, i.e. replace lines 500–501 with:
   ```python
   if LISTERS & seg_heads:
       return True
   if LISTERS & line_heads:  # a lister elsewhere on the line: only a port lookup (lsof) may feed this kill
       if not pids or any("$" in p for p in pids) or not (seg_heads - {"kill"} - SHELLS) <= {"lsof"}:
           return True
   ```
   Add the six shapes above to `test_guard_segments.py` as deny cases (X12–X17). Round 2 I re-run the harness and the suite.

## Checks
- [x] Only owned paths changed (`git diff --stat origin/main -- team/hooks team/settings.json`): yes; `.claude/**` untouched
- [x] Nothing outside scope (`--prune`, `--force-if-includes` and abbreviation handling widen the push denylist, which the card allows as "still denied"; no other guard rule changed)
- [x] Tests exercise the behavior, and none were weakened (scan hits are report prose; new tests fail on the old code)
- [x] Tenancy / idempotency / money / en-es: n/a (hooks); no PII in the guard-paths log (path only, `SECRET` content never written: `test_main_session_allowed_and_logged_without_content`)
- [x] Decisions recorded where needed: none required (B-47/B-116 are backlog items; the card is the record)

## Optional notes (not blocking)
1. **Bash writes are the real hole for B-47 (author already lists it).** Both `tech-lead` and `reviewer` have Bash (`.claude/agents/*.md` `tools:`), so `cat > invai-backend/src/x.ts`, `sed -i`, `tee`, `cp`, `git apply` bypass the path guard entirely. Owner: platform-sre, next card, security-reviewer co-reviews. Suggested shape: in `guard-bash.py`, for `agent_type in {tech-lead, reviewer}` deny redirections (`>`, `>>`, `|& tee`), `tee`, `sed -i`, `cp/mv/rm/mkdir/touch`, `git apply/am/cherry-pick/merge/rebase/checkout/restore/stash pop` whose targets resolve outside the role's trees; `sync.sh restore` stays allowed for the tech lead after approvals.
2. **Delegation gap:** a `tech-lead` can spawn `general-purpose` / `claude` (my G32: `general-purpose` is unrestricted) and have it edit product code. A PreToolUse on `Agent` that denies a tech-lead `subagent_type` outside the 20 role names would close it cheaply. Same later card as note 1.
3. **Fork:** the report verified `agent_type` for a named subagent. A `fork` of the tech lead (`subagent_type: "fork"`) may report `fork`, the parent's name, or nothing; the last two cases fail open (logged only). Worth one more headless probe in the follow-up card so the log in `team/state/guard-paths.log` can be read correctly.
4. **Push hardening (both old and new allow):** the `git push <remote> tag <name>` syntax and bare tag names without `v` (`release-2026-09-28`); `GIT_CONFIG_COUNT/KEY/VALUE` env config; `git config remote.*.mirror|push|push.followTags` in one segment followed by a plain push. Cheap adds: treat `tag` as an argument that denies, and add `git config` of `remote\.\w+\.(mirror|push)` and `push\.` keys to the config rule that already denies `alias.`. Low.
5. **Path guard sharp edges, harmless:** a trailing newline in an allowed path is accepted (the file lands inside `waves/`); a *file* named `reviews` under a wave (`waves/99/reviews`) is writable for the tech lead because only directory components are excluded. Neither reaches code.
6. **Timeout:** `guard-paths.py` has `timeout: 5`. If Claude Code treats a hook timeout as non-blocking, a slow filesystem fails open for restricted roles. Not observed (every probe returned in well under a second); note only.
7. The card's `python3 -m pytest` doesn't run on the system Python (no pytest). The report's `uv run --no-project --with pytest … -B -p no:cacheprovider` form works and leaves no caches; the tech lead may want the card's verification line updated to it.

Re-run for round 2: the suite command above, then the six kill shapes and the three lesson shapes (`kill 123; ps -p 123`, `kill $(lsof -ti :3101); ps aux | grep '[t]sx'`, `pgrep -fl tsx; kill 41234`) through `guard-bash.py` stdin as `backend-engineer`; expected deny ×6, allow ×3.
