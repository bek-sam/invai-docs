---
name: invai-ui-no-build-script
description: invai-ui has no `pnpm build` script — it's a source-only package consumed via link:, so DoD for it is typecheck+lint+test plus consumer (web/floor) typecheck+build.
metadata:
  type: project
---

`invai-ui/package.json` scripts are only `lint`, `format`, `typecheck`, `test`, `playground` — no `build`.
Confirmed 2026-10-01 (T-P7-2): `pnpm build` in `invai-ui` fails with `ERR_PNPM_RECURSIVE_EXEC_FIRST_FAIL`
("Command \"build\" not found"). This matches the CLAUDE.md DoD table (contracts/ui/backend get
typecheck+lint+test; web/floor get typecheck+lint+test+build) — a task card that lists `pnpm build` as
invai-ui verification is slightly off; satisfy it instead by typechecking and building the two consumer apps
against the linked kit (`cd invai-web && pnpm build`, same for invai-floor — both need `VITE_API_URL` set,
e.g. `VITE_API_URL=https://api.example.com`, or they refuse to build for production).

Also: `playground/App.tsx` is not covered by `invai-ui`'s root `tsconfig.json` (`include: ["src"]`), so
`pnpm typecheck` won't catch a broken playground import — verify it separately with
`pnpm exec vite build --config playground/vite.config.ts` (one-off, no dev server/port needed) and delete the
output `playground/dist` after.
