---
name: kit-i18n-in-web-proof
description: How to prove invai-ui kit locale strings (e.g. confidenceBand.*) render in invai-web, and why a node vitest render probe fails
metadata:
  type: reference
---

2026-10-01 T-P7-3: web `src/i18n/index.ts` calls kit `initI18n` (kit en/es JSON into `translation`), then `addResourceBundle(deep, overwrite)` layers web keys on top. One i18next instance comes from `vite.config.ts` `resolve.dedupe`. Proof that works: the build has a single `vendor-i18n` chunk, and web already relies on kit-only keys (`orderState.*` via StatusBadge, `dataTable.*`).

A node-vitest SSR render of a kit component from a /tmp archive fails with `useContext of null` (two React copies, because invai-ui has its own node_modules outside Vite's dedupe), even with `server.deps.inline`. Don't spend time on it; use bundle evidence and the gate screenshot.

Also: guard-bash blocks running a script created in the same Bash call. Write the files in one call and run them in the next. `pnpm exec` in a /tmp copy tries to install, so use `node node_modules/vitest/vitest.mjs run` instead.
