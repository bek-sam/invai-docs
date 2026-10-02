---
name: i18n-regeneration-regression
description: Web `pnpm i18n` regeneration can silently wipe Spanish in es.ts; how to prove it by flattening en/es at base vs head
metadata:
  type: project
---

2026-09-29 T-23-1: `invai-web/src/i18n/es.ts` held hand-added Spanish missing from `scripts/i18n-es.json`, and dynamic `t(\`x.${k}\`)` keys missing from `scripts/i18n-extra-en.json`. `gen-i18n.py` writes `es.get(k, en)`, so a regeneration turned 374 values to English and dropped 91 keys.

**Why:** the author called it "pre-existing keys with no Spanish", but it was a regression caused by the regeneration.

**How to apply:** when a web diff touches `src/i18n/*.ts`, `git show <base>:src/i18n/{en,es}.ts` into the scratchpad and flatten both with a `node --experimental-strip-types` script (dynamic import of the .ts). Compare the count of keys where es==en, and list the keys that had Spanish at base but are English or missing at head. zsh: quote `"${c}:path"` in `git show`.

Round-2 closure check (2026-09-29): also regenerate in a scratch `git archive` (run `python3 scripts/gen-i18n.py` + `./node_modules/.bin/biome format --write src/i18n` directly, since `pnpm` refuses symlinked node_modules) and `diff -r` against committed `src/i18n`. The gitignored `scripts/i18n-es-missing.json` in the worktree can be stale.
