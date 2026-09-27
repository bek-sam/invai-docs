---
name: contract-version-bump-convention
description: How to decide minor vs patch for @invai/contracts while it sits at 0.x, absent the (unbuilt) version-check script
metadata:
  type: feedback
---

When a contract change needs a version decision and no automated check exists ([[t13-2-not-built]]),
bump the **minor** digit, not patch, while the package is 0.x — for any change, breaking or purely
additive.

**Why:** `invai-contracts/README.md` says "bump the minor version on 0.x" for breaking changes, and
every actual CHANGELOG entry to date (0.3.0 additive-only, 0.4.0 with a removal) bumped minor, never
patch — there's no patch-bump precedent in this repo's history. Standard semver also treats a
backward-compatible addition (new enum value, new optional field, new procedure) as a feature (MINOR),
never a fix (PATCH), so both readings agree: minor is right either way.

**How to apply:** on any `invai-contracts` change, check `package.json` version and
`src/compat.ts`'s `CONTRACT_VERSION` together (a test enforces they match) — bump both, write the
CHANGELOG entry with an explicit "Version decision" paragraph naming which rule you followed. Only
touch `FLOOR_COMPAT_BASELINE` when the change is floor-facing (floor/station-facing shapes actually
changed) — leave it alone for web-only or backend-only-tool changes like assistant events.
