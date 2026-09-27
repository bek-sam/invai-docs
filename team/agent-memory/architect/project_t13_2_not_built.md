---
name: t13-2-not-built
description: The T-13-2 contract version-check script (check:consumers, CI version-bump check) was planned but never implemented
metadata:
  type: project
---

`invai-docs/waves/13/T-13-2.md` ("Contract CI and versioning", B-83) planned a `pnpm check:consumers`
script and a CI step that fails if a contract change ships without a version bump. As of wave 17
(2026-09-26) it was never built: no report in `invai-docs/waves/13/reports/`, no `check:consumers`
script in `invai-contracts/package.json`, no matching step in `invai-contracts/.github/workflows/ci.yml`.

**Why this matters:** task cards that say "follow the version-check script from T-13-2 if it exists"
assume it might be there. Check before relying on it — it wasn't there as of T-17-1.

**How to apply:** when a card references T-13-2's tooling, verify first (`ls invai-docs/waves/13/reports/T-13-2*`,
grep `check:consumers` in `invai-contracts/package.json`). If still missing, decide the version bump
by hand and record the reasoning in the CHANGELOG entry, same as [[contract-version-bump-convention]].
If this keeps recurring, it's worth flagging to the tech lead as an actual backlog item rather than
re-deciding by hand each time.
