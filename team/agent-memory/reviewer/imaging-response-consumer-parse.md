---
name: imaging-response-consumer-parse
description: Imaging reviews - parse live imaging responses with the backend's own zod client; closed enums (flag codes) make "additive" codes breaking
metadata:
  type: feedback
---
For any imaging change that adds response values (not just fields), run the real backend client
(`createImagingClient(url, ms, secret)` from invai-backend/src/integrations/imaging/client.ts via
`./node_modules/.bin/tsx /tmp/x.mts`) against imaging on a scratch port with STORAGE=local in /tmp.

**Why:** 2026-09-30 T-P1-2: new `/render/personalization` flag codes (`upscale`, `aspect_mismatch`)
passed all 117 imaging tests but the backend's closed `z.enum` (and the contract enum) rejected them,
making personalizations permanently `failed`. New fields are additive; new enum members are not.

**How to apply:** grep client.ts for `z.enum` on every response the diff touches; prove with a live parse.
