---
name: local-proof-shared-state
description: After an author's local full-stack proof run (run-e2e.sh, a seed into a scratch DB), check that the shared invai-backend/seed-output.json still matches the dev DB
metadata:
  type: feedback
---
2026-09-29 T-23-7 r2: the author seeded scratch DBs through `run-e2e.sh`, and the seed rewrote the shared `invai-backend/seed-output.json` (the E2E helpers read that fixed path). The report said the "shared dev DB [was] untouched". The file's shopId and station token no longer matched the dev DB.
- Check: compare `ls -la seed-output.json` with the run time. Look up `companies` by the file's shopId in the dev DB. Hash the token (sha256 of the full token and of its secret part) against `station_tokens.token_hash`.
- Don't run `run-e2e.sh` yourself from the shared workspace for the same reason.

**Why:** a clobbered token silently breaks every other agent's floor or API E2E until someone reseeds.
**How to apply:** on any card whose proof ran a seed outside the gate. Report it as an operational finding for the tech lead.
