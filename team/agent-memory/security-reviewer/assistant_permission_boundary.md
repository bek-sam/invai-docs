---
name: assistant-permission-boundary
description: ai.assistant.ask is only held by owner/admin/office, all of whom already hold finance.read
metadata:
  type: project
---

`assistantTools(ctx)` (`invai-backend/src/modules/ai/service.ts`) hands every caller of `ai.assistant.ask`
the same fixed tool list, with no per-tool permission filter. Checked 2026-09-26 against
`invai-contracts/src/roles.ts`: only `owner`, `admin` and `office` hold `ai.assistant.ask`, and all three
already hold `finance.read` too — so today the assistant's profit/ad/fulfillment tools expose nothing a
designer or floor role couldn't already reach via `finance.get`/`finance.profit`. No privilege-escalation
finding as of T-17-2.

**Why:** worth re-checking any time a new role is added, a role's permission list changes, or a new
assistant tool exposes data gated by a permission other than `finance.read` (e.g. a future tool over
`vendors.read` or `inventory.read` data) — since `assistantTools` still has no per-tool gate, a role gap
would silently leak through.

**How to apply:** on any card touching `roles.ts` or adding an assistant tool, re-diff `ROLE_PERMISSIONS`
against the tools' underlying data permissions before approving.
