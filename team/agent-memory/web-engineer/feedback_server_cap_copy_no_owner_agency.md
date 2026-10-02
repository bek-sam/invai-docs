---
name: feedback_server_cap_copy_no_owner_agency
description: Error copy for a server-controlled limit must not say "ask the owner" or claim it as the shop's own limit
metadata:
  type: feedback
---

T-P7-3 r2 (2026-10-01): product-designer sent back `assistant.error.spendCap` ("Your shop's AI limit for
today has been reached. Try again tomorrow, or ask the owner to raise it.") because the AI spend cap is a
server setting no shop owner can change, and it can be the platform-wide cap rather than the shop's own —
the copy falsely implied owner agency and shop-specific ownership.

**Why:** copy that names a wrong actor or a wrong scope for a limit sets a false expectation (the owner will
try to "raise it" and can't, or will think it's their shop specifically when it's platform-wide).

**How to apply:** before writing error copy for any cap/limit value, check who actually controls it and
whether it's tenant-scoped or platform-wide. If the reader has no lever to pull, the copy should say only
what happened and when to retry ("Today's AI limit has been reached. Try again tomorrow.") — no "ask X to
fix it" unless X truly can. Applies to credits/quota/rate-limit copy generally, not just the assistant.
