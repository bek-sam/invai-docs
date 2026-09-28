---
name: public-route-review-checks
description: Checks for reviewing session-less token routes (e.g. /l/:token) and shared review worktrees in InvAI
metadata:
  type: feedback
---

2026-09-27 T-19-4 r1:
- Token-in-URL routes: grep `src/api/app.ts` `onError` — it logs `c.req.path`, so any 500 in a `/l/:token`-style route leaks the token despite route-level "never log the token" care. Check the global error logger, not just the route file.
- `mailer.ts` "mail sent" logs `to` (pre-existing); any new feature routing person mail through it inherits that.
- Per-IP buckets use `clientIp()` = first `x-forwarded-for` value: spoofable. Prove with 62 requests on one XFF (60 ok, 2 × 429) and one on a new XFF (ok).
- A co-reviewer may drop proof tests into *my* worktree and share Redis DB 10 (reviewers' shared DB): don't `FLUSHDB` or remove the worktree while foreign untracked files are fresh; delete only my keys and report it.
- `createdb -T invai` worked while other agents were connected elsewhere; a dev copy already had later-wave migrations (0029) applied, and an older worktree's migrate still said "up to date".

**Why:** these were the non-obvious findings and traps on the first auth-less email route review.
**How to apply:** any card adding public/unauthenticated routes or person-facing email; any review in a wave where co-reviewers run at the same time.
