---
name: t23_1_p2_sweep
description: T-23-1 (wave 23 P2 sweep) findings across round 1 and round 2 — i18n drift, CSP, oRPC output stripping.
metadata:
  type: project
---

Round 1: `Alert.data` isn't on the wire (oRPC strips unknown output keys); i18n-es.json/en.ts had a
384-key pre-existing drift; dynamic-key catalogs (`t(\`x.${v}\`)`) live in i18n-extra-en.json by
hand; `<li className="flex ...">` drops its bullet/number.

Round 2 (fixing reviewer/designer r1 findings): `i18n-es.json` (the source `scripts/gen-i18n.py`
reads) can silently drift from the hand-edited, generated `src/i18n/es.ts` for a long time — es.ts
had 374 keys with real Spanish that `i18n-es.json` never had, so any regen replaces them with
English. Before hand-editing i18n JSON files again, diff the generated `.ts` against the source
`.json` first. To flatten a generated `en.ts`/`es.ts` into a flat key→value map for diffing across
commits, don't hand-parse the pretty-printed JS object literal (biome reformats it, unquoting some
keys, wrapping long lines) — `git show <sha>:src/i18n/es.ts > /tmp/es-old.ts` then
`await import(file)` from a `.mjs` script works directly: Node 24's built-in TS type-stripping
erases the `: Messages` / `import type` annotations for free, no esbuild/tsc API needed (the
`typescript` npm package here is v7's native/Go port — `ts.transpileModule` etc. don't exist on
it, only `version`/`versionMajorMinor`).

Also: some `t(...)` calls use a `tr(...)` alias (module-level `i18n.t`, e.g.
`src/lib/errors.ts`) or a template-literal key — both invisible to `extract-i18n.py`'s
`\bt\(\s*"..."` regex — so their keys silently depend entirely on `i18n-extra-en.json` /
`i18n-es.json` having them by hand; they don't show up as "missing" until something else removes
them.

CSP: `vite.config.ts`'s `prodCsp` (served by both `vite preview` and the real prod build) sets
`img-src 'self' data: blob: https:` — no plain `http:`. Local MinIO is HTTP-only, so any
`SignedImage`/presigned-URL preview tested against `vite preview` (not `pnpm dev`) shows a broken
image with `net::ERR_BLOCKED_BY_CSP`, even though the feature and the CSP policy are both correct
(real S3 is HTTPS). Not a code bug — don't "fix" it by loosening prodCsp locally.
