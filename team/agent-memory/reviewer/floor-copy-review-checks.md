---
name: floor-copy-review-checks
description: Floor station copy/i18n review recipe - VITE_API_URL build, base-archive red proof for vitest, e2e text clash grep, ResultPanel tones
metadata:
  type: reference
---
2026-09-30 T-P1-5:
- invai-floor `pnpm build` fails without `VITE_API_URL` (CSP guard in vite.config); run `VITE_API_URL="" pnpm build`.
- Prove a new floor vitest is red on base: `git archive <sha>~1 | tar -x -C /tmp/x`, symlink node_modules, copy test in, run vitest.
- Copy changes on result headings: grep `e2e/*.spec.ts` for getByText substrings that the new text could duplicate (Playwright strict mode).
- QcStation tones: pass=ok (green), fail=warn (amber), error=blocked (red); authors sometimes misreport fail as blocked.
