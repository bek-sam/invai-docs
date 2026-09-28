# Review of T-20-4 (round 1)

- Reviewer: reviewer on claude-sonnet-5
- Author: platform-sre on claude-opus-5-5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 uv run --no-project --with pytest python3 -B -m pytest invai-docs/team/hooks/tests -q -p no:cacheprovider` | `57 passed, 302 subtests passed in 8.91s` (matches report) |
| `python3 -c 'import json;json.load(open("invai-docs/team/settings.json"))'` | parses OK |
| `git -C invai-docs show 9a1a445 --stat` | `team/hooks/guard-bash.py`, `team/hooks/guard-paths.py`, `team/hooks/tests/test_guard_paths.py`, `team/hooks/tests/test_guard_segments.py`, `team/settings.json`, `waves/20/reports/T-20-4.md` — all inside owned paths |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-docs 9a1a445^` | no `.skip`/`.only`/loosened-assertion hits in the new test files (only report-text keyword noise) |
| `diff invai-docs/team/settings.json .claude/settings.json` | live `.claude/settings.json` does not yet have the new hook entry, and `.claude/hooks/guard-paths.py` does not exist — sync correctly not run yet (card: "After both approvals only") |
| Own adversarial `guard-paths.py` probes (own scratch workspace, `CLAUDE_PROJECT_DIR` set) | `..` traversal that escapes `reviews/` for the reviewer role → deny (2); `..` traversal collapsing back inside an allowed tree → allow (0); double-slash path under `reviews/` → allow (0); `NotebookEdit` outside tech-lead paths → deny (2) — all as expected |
| Own adversarial `guard-bash.py` probes (payloads as files, since the *live* installed guard-bash.py, not yet updated by this card, itself blocked a Bash command containing the literal push text — same false-positive class the author reported) | `git push origin main && git push -f` (tech-lead) → deny; `bash -c "git push origin main"` (safe push) → allow; `echo $(git push origin main)` (safe push) → allow; `A=--for; B=ce; git push origin main "$A$B"` (flag built from two concatenated vars) → deny; `GIT_SSH_COMMAND=x git push -f origin main` (env-var prefix) → deny; two safe pushes chained with `;` → allow; `git push origin main; kill $(cat pidfile)` as backend-engineer → deny (existing push-role rule, unrelated to this card) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Path guard denies tech-lead/reviewer writes outside their trees, names allowed paths + "write a card for the owner" | yes | `test_denial_names_paths_and_says_write_a_card`; my own probes reproduced the exact message text for both roles |
| 2. Agent known from `agent_type`; missing → allow + one-line log (no content); main sessions unblocked | yes | Source documented in report (headless probe on Claude Code 2.1.283); `test_main_session_allowed_and_logged_without_content`, `test_subagent_without_type_allowed_and_logged`, `test_default_log_lives_in_team_state_and_is_ignored` all pass; log line format confirmed to hold only time/caller/tool/path |
| 3. Other roles unaffected | yes | O01–O05 pass (`backend-engineer`, `platform-sre` unaffected; only exact/prefixed/case-folded `tech-lead`/`reviewer` names are restricted; `tech-lead-helper` is not) |
| 4. B-116 segment-aware push/kill rules | yes | B01–B13 (previously false-denied) now allow; D01–D35 (danger, chained/nested/`bash -c`/`$()`/backtick/env-prefix) still deny; K01–K07 (literal-PID kill next to a lister) allow; X01–X11 (lister-fed kill) deny. My own extra probes (var-concat flag, env-var prefix, doubled safe push) matched expected outcomes |
| 5. Adversarial tests exist and pytest passes | yes | `python3 -m pytest invai-docs/team/hooks/tests -q` equivalent (via `uv run --with pytest`, since the system `python3` lacks pytest — same workaround the author used and documented) → `57 passed, 302 subtests passed` |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git show 9a1a445 --stat`): `team/hooks/**`, `team/settings.json`, `waves/20/reports/T-20-4.md`. `.claude/**` untouched (confirmed by `diff` above and `git status` showing `.claude/` still untracked/unsynced).
- [x] Nothing outside scope: no other guard rule's behavior changed except the documented push/kill segment logic; builder-role path checks explicitly deferred to a later card, as the card's "Out of scope" allows.
- [x] Tests exercise the behavior, and none were weakened: all new tests (`scan-test-weakening.sh` clean; no `.skip`/`.only`/`fixme`; assertions check both allow and deny sides with concrete stderr message checks).
- [x] Tenancy / idempotency / money / en-es: not applicable (this card is a team-tooling hook, not product code; no `company_id` tables, no money, no user-facing copy).
- [x] Decisions recorded where needed: none needed — this is an implementation of an already-accepted backlog item (B-47, B-116), not a new cross-cutting decision.

## Optional notes (not blocking)
- The card also requires a security-reviewer co-review (risk flag `auth (guard)`); no `T-20-4-security-reviewer-r1.md` exists yet in `waves/20/reviews/` as of this review. The card can't be pushed until that file also says `approve`.
- `role_of()` case-folds and strips a plugin prefix from `agent_type` before matching; this makes the restriction slightly broader than a literal `"tech-lead"`/`"reviewer"` match (e.g. `"Tech-Lead"`, `"x:tech-lead"` are also restricted). This only tightens the control, never loosens it, so it's not a concern.
- Any argument to `git push` containing a literal `$` is treated as dangerous and denied outright (not just resolved substitutions) — this is a deliberate, documented conservative choice ("write push arguments literally") and matches the card's intent to fail closed on unreadable input.
