---
name: gated-contract-commits
description: How to land a contract change whose consumer mirror/test must go first (backend REPRINT_REASONS type mirror, fees.test.ts pinning a CHANNEL_RULES default) without turning the shared working copy red
metadata:
  type: project
---

Some contract edits break a consumer *test or typecheck* even though they are additive: the backend keeps a
type-only mirror of `REPRINT_REASONS` in `invai-backend/src/db/schema/production.ts` (`enumText`, no CHECK
constraint), and `invai-backend/src/modules/finance/fees.test.ts` asserts the exact `CHANNEL_RULES.<ch>.fees`
default. Because every consumer links to the contracts *working copy*, such an edit sitting in the tree makes
the gate red for everyone.

**Why:** T-22-1 (2026-09-28): the tech lead required green consumers at the wave 20 gate; the reprint-reason
append and the TikTok 8→6 default each broke a backend check the moment they were in the working copy.

**How to apply:** commit those items separately after the main commit, `git format-patch` them into
`invai-docs/waves/<n>/patches/`, then `git revert` them on main (no reset/checkout in the tree) so the working
state is the green commit; the tech lead cherry-picks the original SHAs when the consumer card lands. Grep
`invai-backend/src/db/schema/*.ts` for a mirror of any enum you extend, and `*.test.ts` for `CHANNEL_RULES`
value assertions, before choosing what goes in the main commit.
