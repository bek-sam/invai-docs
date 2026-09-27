---
name: project-t18-5-market-signals
description: T-18-5 (wave 18) built market chips/badge/votes/niche picker in the assistant and design page; known e2e gaps routed to other owners, not fixed by editing their tests
metadata:
  type: project
---

T-18-5 (2026-09-27) added the 4 market tool chips, 3 starters, a "Sample data" badge, vote cards
bound to `RecommendationRef.id` (assistant stream + stored message), and a niche chip/picker
(`components/market/**`) to `invai-web`. Three issues in QA's `e2e/market.spec.ts` (not mine to
edit) were found and routed rather than worked around:

1. **`ai.assistant.ask()` streaming always logs one `net::ERR_ABORTED`** on the POST, even with a
   200 response and a fully-received stream — reproduced on a pre-existing wave-17 tool question
   too, so it's `@orpc/client`'s event-iterator fetch handling, not anything wave-18-specific.
   Routed to ai-engineer/architect + qa-engineer (whose `watchPage` zero-failed-requests check
   will fail on *every* assistant answer until this is fixed or the check is relaxed).
2. QA's `askStarter` helper uses a non-exact `getByRole('button', {name: text})`; once two
   conversations share a starter's exact title (which happens by design when hunting for a
   starter that yields votes), it collides with the sidebar history and throws "strict mode
   violation".
3. A locale-before-login e2e test breaks the shared `loginAs` helper (`getByLabel("Email")` only,
   but the field is "Correo" once Spanish is set first).

**Why this matters for later cards:** don't assume `e2e/market.spec.ts` red = your code is wrong;
check whether the failure reproduces with a pre-existing (non-market) code path or an unrelated
test/helper assumption first. See [[feedback-dev-csp-needs-build-preview]] for the CSP-related
setup this card also needed.

**How to apply:** if asked to make `e2e/market.spec.ts` fully green, the fix is in
`e2e/helpers/ui.ts` (`loginAs`) and `e2e/market.spec.ts` (QA-owned) plus possibly
`ai/service.ts`'s streaming (ai-engineer-owned) — not in `invai-web/src/routes/_app/assistant.tsx`
or `components/market/**`.
