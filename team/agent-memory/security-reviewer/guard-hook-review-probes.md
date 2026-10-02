---
name: guard-hook-review-probes
description: How to probe guard-bash.py push rules in a review without tripping the live hook or pushing anything; the exemption-tolerates-prefix class of gap
metadata:
  type: feedback
---

Probe guard-bash.py from a Python file written with the Write tool that imports `run`/`decision` from `team/hooks/tests/test_push_stamp.py` (`git archive <sha> team/hooks` into /tmp, copy `.claude/settings.json` beside it); never put push/force text in a Bash heredoc, the live hook denies the heredoc itself. Stamps only via `INVAI_GATE_STAMP_PATH`; git mechanism checks in /tmp bare repos driven by Python subprocess.

**Why:** 2026-10-02 T-P8-3 r4 (S-47/S-49): a heredoc containing `--force`/`:main` was blocked before the probe ran; the Write-tool route worked. The r2 (S-47) and r3 (S-49) gaps were both of one shape: an exemption that checks its own words but tolerates the rest of the command (`export HOME=`, `XDG_CONFIG_HOME=`, `PATH=` prefixes, zsh `function 'git'`), so an exact-form allowance is redirected by git's own config lookup.

**How to apply:** for any guard exemption, test the surrounding items, not only the exempt command's words: env assignments that git reads (HOME, XDG_CONFIG_HOME, PATH, GIT_*), quoted function names (zsh accepts `function 'git'`, bash does not), shadow binaries on PATH, and lexer quirks (`2 >&1` lexes like `2>&1`). Nothing beyond the open S-46 launcher class is a new capability; weigh blocking against what OI answers scoped.
