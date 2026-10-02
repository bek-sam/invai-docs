---
name: ts7-lib-dts-location
description: TypeScript 7's own node_modules/typescript/lib has no lib.*.d.ts files; they ship in the platform package (e.g. @typescript/typescript-darwin-arm64). Also covers Intl.NumberFormat useGrouping vs minimumGroupingDigits.
metadata:
  type: reference
---

TypeScript 7.0.2 (the native/Go-ported compiler) is a thin loader: `node_modules/typescript/lib/`
only has `getExePath.*`, `tsc.js`, `version.*` — no `lib.es5.d.ts` etc. The real lib files (and the
authoritative `Intl.NumberFormatOptions` etc. interfaces) live under the platform-specific optional
dependency pnpm installs, e.g.
`node_modules/.pnpm/typescript@7.0.2/node_modules/@typescript/typescript-darwin-arm64/lib/lib.*.d.ts`
(swap `typescript-darwin-arm64` for your platform from `typescript`'s `optionalDependencies`).

**How to apply:** `read-before-change`'s "check node_modules before using an API" for TS 7 means
checking that platform package's `lib/`, not `typescript/lib/` directly — grepping the latter will
wrongly look empty/missing. Confirmed on T-P3-3: `minimumGroupingDigits` is absent from
`Intl.NumberFormatOptions` there, and **also has zero effect at runtime** (Node 24.21 / ICU 78.3
silently ignores it, confirmed via `resolvedOptions()`) — so for Intl options specifically, a
missing type is a real signal, not just a typing gap, worth a quick runtime check too before
assuming a cast would even help.

**Round 2 correction:** the *standard* equivalent, `useGrouping: "always"`, IS typed and DOES work —
don't let the `minimumGroupingDigits` dead end rule out the whole grouping-control area.
`lib.es2023.intl.d.ts` (in the same platform package, `lib/`) augments
`NumberFormatOptionsUseGroupingRegistry` with `always`/`auto`/`min2`; that only resolves to those
string literals (not just `boolean`) when the tsconfig `lib` array includes `"ES2023"` or later —
check `tsconfig.json`, not just that the `.d.ts` file exists. Confirmed working, no cast, in Node
24.21: `new Intl.NumberFormat("es",{style:"currency",currency:"USD",useGrouping:"always"})` gives
`"1.234,56 US$"` and reproduces `en`'s existing output byte-for-byte. Prefer the native option over
hand-rolled `formatToParts` re-grouping once you've confirmed it exists — don't stop at the first
option name that turns out to be unimplemented.
