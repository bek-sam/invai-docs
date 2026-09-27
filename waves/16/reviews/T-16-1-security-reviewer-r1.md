# Review of T-16-1 (round 1)

- Reviewer: security-reviewer on Opus 5.5
- Author: platform-sre on Opus 5.5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `python3 -B -m unittest discover -s invai-docs/team/hooks/tests` | `Ran 35 tests in 6.442s OK` (includes T-16-2's tests, run together) |
| Fed crafted `PostToolUse`/`Stop` JSON directly to `post-edit-check.py`, `track-verify.py`, `verify-gate.py` on stdin, with `INVAI_HOOK_STATE_DIR` pointed at a scratch dir so the shared `.claude/state/` was never touched | see findings and checks below |

## Acceptance criteria (as they relate to my adversarial mandate)
| # | Met? | Evidence |
|---|---|---|
| 2 Fails open, fast | met | malformed/empty JSON to all three hooks → exit 0, no output, no exception surfaced |
| 3 Tracker parses verify commands correctly, rejects fakes | **mostly met, one gap** | see finding 1 |
| 4 Gate blocks once, message names exact commands, `stop_hook_active` allows | met | reproduced the block message and the `gate_blocked_for` re-stop-allow behavior |
| 5 No false blocks | met | see "fake-check attempts correctly rejected" below |
| Fast-check file-path handling can't be turned into command injection | met | see finding 2 (informational; no injection found) |

## Attempts to fake "checks passed" — results
I simulated an `Edit` on `invai-backend/src/modules/orders/service.ts` (marks the repo pending), then fed each of the following as the following `Bash` `PostToolUse` event, then checked whether `verify-gate.py`'s `Stop` still blocked:

| Attempted fake | Credited as a passing check? |
|---|---|
| `echo pnpm test` | No — still blocks (tool is `echo`, not recognized) |
| `true # pnpm test` | No — still blocks |
| `pnpm test \|\| true` | No — still blocks (`_known_success` correctly treats the `\|\|`-guarded segment as unproven) |
| `pnpm test --run nothing` | No — still blocks (a positional arg after `test` disqualifies it, by design) |
| `pnpm test -t zzz-no-match` | No — still blocks (any `-t`/filter flag disqualifies it, regardless of match count — this is actually stricter than the minimum bar) |
| `pnpm test` with no output at all (the honest case) | Credits `test` only, still blocks on missing `typecheck`/`lint` |

All of the specific attacks named in my brief are correctly rejected. Good, careful work — `classify()` in `invai_hooklib.py` disqualifies on any positional argument or known filter flag rather than trying to special-case each one.

## Blocking findings

1. **`invai-docs/team/hooks/invai_hooklib.py:187-210, 343-388` (`_known_success`/`parse_verifications`, used by `track-verify.py`) — a check whose real output is hidden by a truncating pipe stage is credited as passed even when it actually failed.**

   The gate infers success only from (a) the shell's own `&&`/`;` exit-status chaining and (b) a `FAIL_MARKERS` regex over the *captured* `tool_response.stdout/stderr` — which, for a piped command, is only the output of the pipeline's last stage, not the full output of the earlier (real) command. When the trailing stage is a truncating filter like `head`, a real failure can be typed and printed but never appear in the captured text.

   Reproduced end to end (state dir isolated in scratch, no shared state touched):
   1. `Edit` event on `invai-backend/src/modules/orders/service.ts` → `Stop` correctly blocks: `"You edited code after its last successful checks. Before you finish, run: ... pnpm typecheck && pnpm lint && pnpm test"`.
   2. `Bash` `PostToolUse` event, `command: "pnpm test | head -3"`, `tool_response.stdout` set to a realistic truncated head of a **failing** vitest run (just the `RUN` banner and the file name — no `FAIL`/`failed` text, which real vitest/pytest failure summaries print at the *end* of the output, past where `head -3` cuts off).
   3. Also sent honest `pnpm typecheck` and `pnpm lint` events with clean (empty) output, to isolate the `test` bypass from the other two checks.
   4. Resulting state file: `"ok": {"test": <ts>, "typecheck": <ts>, "lint": <ts>}` — all three now considered satisfied.
   5. `Stop` event → **no output at all: the gate allows the stop**, believing `pnpm test` passed, even though the simulated real run failed and nothing about that failure ever appeared in what the gate inspected.

   This is exactly the class of abuse item 2 of my brief asks about, and it lands on precisely the mechanism ("Verification gate abuse... a false-block or loop risk") the whole wave exists to close ("Unverified 'done'... a builder that skips its checks is caught only at review or the gate"). Unlike `echo pnpm test` or `pnpm test || true` (both correctly rejected, see table above), `pnpm test | head -N` (or `| grep -v ...`, or any filter that can eat the summary line) is an ordinary way to keep terminal output short, not an exotic evasion — an agent could do this by habit, with no intent to defeat the gate, and it would still silently mark a real failure as "verified."

   The report already names this in "Known gaps and follow-ups" ("Piped checks rely on output failure markers... `pnpm test \| head -3` could hide a failure line. `pipefail`, or no pipe at all, is exact."), so it isn't hidden — but disclosure doesn't close the gap, and my brief specifically asked me to prove or rule out this exact scenario. I'm treating it as blocking because it directly undermines acceptance criterion 3/5's purpose (the tracker must not be fooled) for a very ordinary command shape, not because the author was dishonest about it.

   **Suggested fix (for platform-sre, not mine to make):** don't credit a piped segment as `"sure"`/`"piped"` from output inspection at all unless `pipefail` is set (drop the `not FAIL_MARKERS.search(output)` fallback for the non-`pipefail` case, i.e. flip the default from "credit unless a failure marker is seen" to "credit only when we can be sure" — the same posture already used for `||`-guarded and positional/filtered runs). That will push agents whose output genuinely got cut to just re-run without a pipe, which matches the hook's own stated intent ("only its success is certain").

2. **Informational, no vulnerability found — `post-edit-check.py` file-path handling.** I fed `file_path` values containing backticks, `$(...)`, `;`, embedded `rm -rf`, spaces, and `../../../../etc/passwd.ts` directly to the hook. No injection occurred and no marker file was created by an embedded `` `touch ...` `` payload, because `subprocess.run([...])` is always called with a list of arguments (never `shell=True`), so shell metacharacters in the path are inert — they're passed to `biome`/`ruff`/`tsc` as one literal (nonexistent) filename argument, which the tool reports as "file not found," nothing more. Path traversal outside a repo correctly falls through `find_repo()` returning `None` (exit 0, no lint run). This satisfies item 3 of my brief; I'm recording it as a checked-and-clear item rather than a finding.

## Checks
- [x] Only owned paths changed (`git -C invai-docs diff --stat` for `e97c71a`: matches the card's owned paths, including the added `invai_hooklib.py` the wave file already grants to T-16-1)
- [x] Nothing outside scope
- [x] Tests exercise the behavior; no `.skip`/loosened assertions/mocks of the unit under test found in the diff
- [x] Fails-open behavior verified directly (malformed/empty input to all three hooks: exit 0, silent)
- [ ] Verification-gate integrity: **not fully sound** — see finding 1

## Recommendation
Send finding 1 back to platform-sre alongside T-16-2's finding: tighten `parse_verifications`'s pipe handling so a truncating filter can't mask a real failure. I'll re-run the same end-to-end reproduction (steps 1–5 above) against the fix before approving.
