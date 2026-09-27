# Review of T-16-1 (round 2)

- Reviewer: security-reviewer on Opus 5.5
- Author: platform-sre on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `python3 -B -m unittest discover -s invai-docs/team/hooks/tests` | `Ran 43 tests in 7.206s OK` |
| End-to-end reproduction of round-1 finding 1 (`pnpm test \| head -3` masking a real failure), same isolated-state-dir method as round 1 | now correctly **not** credited, and the Stop message names the reason (see below) |
| Same, with `set -o pipefail; pnpm test \| head -3` prefixed | now correctly credited (see reasoning below on why this is safe) |

## Round-1 finding — verified fixed
`invai_hooklib.py`'s `parse_verifications` no longer infers success from `FAIL_MARKERS` text-scanning; a piped
segment ("piped" status) is only credited when the command explicitly sets `pipefail` (`set -o pipefail` /
`set -eo pipefail` / etc., detected by `w[0] == "set" and "pipefail" in w` with the `-o`/`-eo` flag check).

Reproduced end to end in an isolated `INVAI_HOOK_STATE_DIR` (no shared state touched):
1. `Edit` on `invai-backend/src/modules/orders/service.ts` → repo marked pending.
2. `Bash` `PostToolUse`, `command: "pnpm test | head -3"`, `tool_response.stdout` a truncated, failure-marker-free
   head of a run that actually failed → **not recorded** in `state["repos"][...]["ok"]` (only `typecheck`/`lint`,
   sent honestly in separate events, appear).
3. `Stop` → **blocks**, with the new line: `"Run them without a pipe: \`| tail\` or \`| head\` hides the exit
   code, so a piped run doesn't count (unless the command starts with \`set -o pipefail;\`)."`
4. Same command prefixed with `set -o pipefail;` → now credited. This is safe, not a re-opened hole: the
   `Bash` tool only ever emits a `PostToolUse` event (which is all `track-verify.py` listens to) when the
   *whole* command exits 0; under `pipefail` a real `pnpm test` failure would make the pipeline's exit code
   non-zero, so the tool call would instead fire `PostToolUseFailure`, which `track-verify.py` never sees. So
   crediting a `pipefail`-guarded pipe is exactly as trustworthy as crediting an unpiped command.

No new gaps found in this file's part of round 2 (`post-edit-check.py` itself is unchanged from round 1; the
`test_fast_check.py` diff is a mechanical adjustment for the new second `PreToolUse` matcher entry, not a
behavior change).

## Checks
- [x] Only owned/granted paths changed for this card's part of `0fb800b`: `invai_hooklib.py`, `verify-gate.py`,
      `settings.json` (the second `PreToolUse` entry — its own hook, `guard-memory-path.py`, is T-16-2's per
      the wave-file grant, reviewed there), `tests/test_verify_hooks.py`, `tests/test_fast_check.py`
- [x] Nothing outside scope
- [x] Tests exercise the fix; no `.skip`/loosened assertions found in the diff
- [x] Round-1 blocking finding closed with a real reproduction, not just a code read

## Recommendation
Approve T-16-1. My round-1 finding is closed with evidence. `guard-memory-path.py` and the here-string/`npx`
prefix work are reviewed under T-16-2, where they're owned.
