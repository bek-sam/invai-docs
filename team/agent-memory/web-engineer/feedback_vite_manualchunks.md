---
name: feedback-vite-manualchunks
description: When Vite/Rollup warns "chunks larger than 500 kB", check what's actually inside the named chunk before assuming a tree-shaking bug
metadata:
  type: feedback
---

A Rollup chunk's auto-generated filename (`createLucideIcon-<hash>.js`) names ONE of the modules
inside a merged shared chunk, not necessarily the bulk of its content. On T-23-1 a 632 kB "icon"
chunk turned out to be react+react-dom (found by grepping the built file for `react.transitional.
element` / `isReactComponent` strings) — Rollup's default chunking merges every module shared by
2+ output chunks into a growing common blob, and in an app with dozens of routes each importing a
couple of shared libs, that blob ends up containing most of react/radix/lucide/etc. regardless of
which single module happened to give it its name.

**Why:** wasted time suspecting a lucide-react tree-shaking bug (checked `sideEffects: false`,
the `.mjs` barrel's per-icon re-exports, counted 93 used icons vs 6329 exported) before actually
inspecting the chunk's bytes.

**How to apply:** before treating a chunk-size warning as a tree-shaking problem, `grep` the
built file for a few tell-tale strings from the suspected library. If it's a vendor blob, add
`build.rollupOptions.output.manualChunks(id)` bucketing by `node_modules/<pkg>` path instead of
trying to fix tree-shaking. This doesn't reduce total bytes shipped, only reorganizes which file
holds them — check the actual chunk-size-warning threshold (Vite's default is 500 kB raw per
chunk) is what the card means by "bundle size", not total initial JS.
