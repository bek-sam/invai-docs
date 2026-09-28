---
name: contract-review-checks
description: Fast, proven checks for reviewing invai-contracts cards (permission walk, consumer typecheck, fail-on-base, zsh echo trap)
metadata:
  type: feedback
---

Checks that worked for contract cards (2026-09-27 T-19-1):
- Walk procedures from the backend's link: `cd invai-backend && node --import tsx -e 'import("@invai/contracts").then(m=>...listProcedures(m.contract)... m.PROCEDURE_PERMISSIONS[p.path])'` prints method, path and permission per procedure. Use it to verify the README count and the permission matrix.
- web, floor and backend `node_modules/@invai/contracts` are symlinks to the local repo, so consumer `pnpm typecheck` reflects the uncommitted or new contract directly.
- Appending a value to `ALERT_KINDS` breaks web `alertKindLabel` (an exhaustive switch, TS2366); check wave.md for a grant before blocking.
- Version pinning: only the newest wave's test pins `CONTRACT_VERSION` exactly; older tests use `isContractVersionAtLeast`. That is not a weakening.
- zsh: `echo ====` fails ("= not found", equals expansion) and aborts `;`-chained cats. Use `echo '----'`.

**Why:** saved time and avoided a false "missing file" read.
**How to apply:** on any `invai-contracts` review.
