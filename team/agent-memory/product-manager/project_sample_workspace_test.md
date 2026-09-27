---
name: sample-workspace-test
description: Which flag means "sample workspace" in InvAI specs - isSampleWorkspace, not companies.demo
metadata:
  type: project
---

2026-09-27 W18/W19 spec reviews: "sample workspace" = `isSampleWorkspace(companyId)` / `realCompanySql()` in `invai-backend/src/modules/tenancy/demo-flag.ts` (demoOwnerUserId set or settings.demoRetiredAt). `companies.demo = true` is NOT the test: seeded Desert Bloom has demo=true and gets real-shop behavior.

**Why:** the tech lead's resolution said `companies.demo`; the code comment says otherwise. Specs citing the wrong flag would make mock rules skip the seed shop.

**How to apply:** in any spec that gates on sample workspaces (mock rule, digest skip), cite isSampleWorkspace. Related: mock outside data only outside production or in sample workspaces (scope.md fence, 2026-09-27).
