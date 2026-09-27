---
name: guard-hook-bypass-patterns
description: Reusable adversarial techniques that found real bypasses in InvAI's shell-command guard and verification-gate hooks (wave 16, T-16-1/T-16-2)
metadata:
  type: project
---

Two bypass classes actually worked against `invai-docs/team/hooks/*.py` (opus-authored, wave 16) and are
worth retrying on every future guard/gate change, not just this one.

1. **Unrecognized wrapper-command prefixes defeat any parser that strips a fixed prefix list before reading
   the "real" command.** `guard-bash.py`'s `PREFIX_CMDS`/`_strip_prefix()` knew about `sudo, env, command,
   exec, nice, ...` but not `npx`. Feeding `npx git push origin main` (agent_type a normal subagent role) made
   the whole command look like a single unrecognized `npx ...` call, so `git_rules()` was never invoked and
   the push sailed through — same for `npx git add -A`, `npx git stash`, `npx pkill -f node`, `npx pnpm
   install`, and even the pre-existing anchored `aws` deny rule (`npx aws s3 rm ...`). The tell: a sibling
   file written by the same author for a different hook (`invai_hooklib.py`, used by `track-verify.py`)
   already listed `npx` in its own prefix list — the two parsers had silently diverged.
   **How to apply:** whenever a guard/deny hook strips known prefixes before matching, test it with `npx`,
   `pnpm dlx`, `yarn dlx`, `bunx`, `corepack`, and any other wrapper binary in this stack's toolchain, not just
   `sudo`/`env`/`command`. Also diff the prefix lists across sibling hook files in the same PR — if one hook's
   parser knows a prefix the other doesn't, that's the gap.
2. **A verification/self-report gate that infers "the check passed" from captured process output (regex for
   failure markers) can be fooled by piping the real command through a truncating filter** (`pnpm test | head
   -3`) so the failure summary, which most test runners print at the very end, never appears in what got
   captured. `echo pnpm test`, `pnpm test || true`, `pnpm test --run nothing`, and a `-t`/filter flag matching
   zero tests were all correctly rejected by InvAI's `track-verify.py` — only the truncating-pipe form worked.
   **How to apply:** when reviewing a "did the check really pass" hook, test the `|| true`/`echo`/filter-flag
   family (usually already handled) but specifically also try `<real check> | head -N` and `<real check> |
   grep -v <noise>` with a captured output that lacks the runner's final pass/fail line — that's the one most
   authors miss because it isn't an intentionally adversarial-looking command.

See `invai-docs/waves/16/reviews/T-16-1-security-reviewer-r1.md` and
`T-16-2-security-reviewer-r1.md` for the full reproductions.
