---
name: push-guard-detection-bypass-probes
description: Probe set that beat guard-bash.py's push detection in T-P8-3 r2 (launchers, git-push binary, help.autocorrect, docs-repo carrier); reuse on every push-guard review
metadata:
  type: project
---

The guard's push rules fire only when the lexed head basename is `git` and the subcommand word is `push`.
So probe heads it doesn't strip and subcommands that aren't literally `push` (2026-10-01, T-P8-3 r2, S-46/S-47/S-48):
- Launchers: `env -S "<cmd>"`, `caffeinate -i`, `stdbuf -oL`, `xcrun`, `script -q /dev/null`, `screen -dm`, `osascript -e`, `awk 'BEGIN{system()}'`, `expect -c spawn`.
- `$(git --exec-path)/git-push origin main` (head `git-push`), and `git -c help.autocorrect=immediate psuh [--force]` (git runs `push`; also beats the force guard).
- Docs exemption as a carrier: `git -C <DOCS> fetch <code repo> main:refs/heads/x` then `push <code remote url> x:main`; `git config remote.origin.pushurl` is not blocked.

**Why:** the one-form check (`CODE_PUSH_FORM.fullmatch` on the whole command) is solid against wrappers, so the remaining risk is detection, not form.
**How to apply:** run the probe as `tech-lead` with `INVAI_GATE_STAMP_PATH` pointing at a missing file; any `allow` on a non-docs push is a bypass. My own role can't run even a `/tmp` push for a scratch demo (the live hook denies it): prove the chain with `fetch` only and the guard's decision. The durable fix is remote-side (rulesets), not more blocklist.
