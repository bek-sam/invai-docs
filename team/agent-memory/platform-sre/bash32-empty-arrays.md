---
name: bash32-empty-arrays
description: macOS default /bin/bash is 3.2.57; `"${arr[@]}"` on an empty array errors under `set -u`
metadata:
  type: project
---

macOS ships `/bin/bash` 3.2.57 by default (confirmed via `bash --version` on this machine), Bash
3.x's last release. Under `set -u`, expanding `"${arr[@]}"` when `arr` is a declared-but-empty
array throws `unbound variable` — fixed in Bash 4.4+, but this machine's `/bin/bash` never gets
that fix.

**Why:** hit this writing `invai-infra/scripts/gate.sh` / `scripts/gate/lib.sh` (T-23-6): an
`extra_env=()` array passed as `env "${extra_env[@]}" cmd` broke every suite with
`extra_env[@]: unbound variable` the moment the array was empty (the common case).

**How to apply:** in any new `invai-infra/scripts/*.sh` under `set -u`: guard with
`"${arr[@]:-}"` plus a `[ -z "$x" ] && continue` inside the loop, or branch on
`[ "${#arr[@]}" -gt 0 ]` before expanding. Test scripts on the empty-array path, not just a
populated one.
