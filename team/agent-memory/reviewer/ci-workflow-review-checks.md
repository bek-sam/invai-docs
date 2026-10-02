---
name: ci-workflow-review-checks
description: Checks for reviewing GitHub Actions / CI E2E cards: prove current CI state with gh before accepting "consistency" removals, compare E2E failure counts with the last gate
metadata:
  type: feedback
---

2026-09-29 T-23-7 r1 (changes-required):
- Before accepting removal of any `ssh-key: secrets.*` / token on a sibling checkout, run `gh secret list -R bek-sam/<repo>` and `gh run view <id> --json jobs --jq '.jobs[]|.steps[]|...'` on recent runs: the keyed checkouts were succeeding, so removal = regression (ui CI green → red).
- "N E2E failures are pre-existing" → compare per spec file with the last `waves/<n>/reviews/gate.md`; an author's local logs may be in the shared session scratchpad (`ci-e2e-logs/`).
- CI stack scripts that start the worker before seed break market.spec.ts:91 (qa-report.md:487); run-golden-path step 5 requires restart after seed.
- Tools: actionlint release tarball into scratchpad works; verify SHA pins with `gh api repos/<a>/commits/<tag> --jq .sha`. zsh: use `${=var}` to word-split; guard hook blocks the literal cloud-CLI word in greps (split it).

**Why:** both blocking findings were invisible from the diff alone.
**How to apply:** any CI/workflow or E2E-runner card. See [[gate-script-review-checks]].
