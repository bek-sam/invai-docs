---
name: floor-screen-check
description: How to script floor-tablet screenshots outside the E2E suite (pairing, language, station-switch limits)
metadata:
  type: project
---

For a throwaway floor screenshot script (not a committed spec): the seeded "Press 1" station
token (`seed-output.json`) is pinned to `kind=press` server-side, so `StationShell.tsx`'s
`canSwitch = !fixedKind` is false and the Settings menu never lists other stations — you can only
ever see the Press screen with that token. To reach QC/pack too in one run, issue a fresh unfixed
("any station") token through the owner API first (`owner.stations.create({kind:null})` then
`.stations.issueToken`), exactly the pattern `invai-floor/e2e/press.spec.ts` already uses; still
use the seed token for the read-only lookups that build the press test case.

`LangToggle` (`invai-floor/src/components/LangToggle.tsx`, also used pre-login on
`SetupScreen`/`LoginScreen`) renders the raw lowercase `"en"`/`"es"` text — the visible uppercase
is CSS `text-transform` only. Target it with `getByRole("button", { name: "es", exact: true })`,
not `"ES"` with `exact: true` (that times out).

A plain `node script.mjs` under `/tmp` can't import a repo's workspace packages directly:
`@invai/contracts` resolves to bare-specifier `.ts` source that needs the repo's tsx/ts-node loader.
Fix: symlink the target app's `node_modules` next to the throwaway script
(`ln -s <repo>/node_modules /tmp/<scratch-dir>/node_modules`) so real deps (`@playwright/test`,
`@orpc/client`) resolve, and hardcode the handful of workspace-only constants you need (e.g.
`CONTRACT_VERSION`/`CONTRACT_VERSION_HEADER` from `invai-contracts/src/compat.ts`) instead of
importing `@invai/contracts` itself.

Related: [[gate-traps]]
