---
name: destructive-guard-review
description: Reviewing "is this a test DB" guards in front of destructive test setup (truncate/reset): probe each opt-in or pin exemption with the dev URL
metadata:
  type: feedback
---

2026-09-29 T-23-0 r3: a guard in front of a global truncate trusted any URL pinned via TEST_*_DATABASE_URL, so the dev URL `…/invai` got past it when pinned. I proved it with a tsx one-off that calls the pure guard (no DB touched).

**Why:** an opt-in exemption lets through exactly the misconfiguration the guard exists to stop (a pasted dev URL), and the README claimed that couldn't happen.
**How to apply:** list every allow branch of a safety guard and feed each one the forbidden input. Before using an assigned scratch Redis DB, check it with `docker exec local-valkey-1 valkey-cli -n N dbsize` (there is no host redis-cli); if it isn't empty, pick an empty one. In zsh, use a shell function, not a `$VAR` holding a command. Related: [[redis-url-redirect-review]].

2026-09-29 T-23-0 r4: the fix compared raw URL pathnames, but pg decodes them (`pg-connection-string` `decodeURI`), so `%69nvai` got past a name denylist. Also run the new guard test file against the base guard in scratch (a pure unit needs no DB), and check the CI workflow's raw DATABASE_URL isn't in the new refused set.
