---
name: contract-consumable-check
description: How to prove a contract card is consumable by the backend when the shared backend tree is red from other agents' WIP
metadata:
  type: feedback
---
When the shared `invai-backend` typecheck is red from other cards' uncommitted WIP, judge the contract by `git archive <commit>` of the backend into a sibling dir (`/Users/bekbolsun/invai/invai-backend-review-<card>`), symlink `node_modules`, run `./node_modules/.bin/tsc --noEmit`, then delete the dir. Capture exit codes with `>/dev/null; echo $?`, not `| tail` (the pipe hides the exit code).

**Why:** T-18-1 r1 (2026-09-27): shared tree failed in T-18-3 WIP; the archive at the stub commit and at HEAD both passed, which isolated the contract from the WIP.
**How to apply:** every contract card review in a wave where backend agents run at the same time. Also check new contract regexes (e.g. `NicheKey`) against the real backend data file.
