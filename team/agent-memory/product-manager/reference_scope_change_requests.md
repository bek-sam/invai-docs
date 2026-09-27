---
name: reference-scope-change-requests
description: Where scope-change requests live and how numbering/escalation works in this repo
metadata:
  type: reference
---

`invai-docs/product/scope-changes/` did not exist before 2026-09-26; I created it filing
SCR-001 and SCR-002 (see [[project-wave17-assistant-analyst]]). Numbering is `SCR-NNN-<slug>.md`,
sequential, zero-padded to 3 digits (per the `scope-change-request` playbook template).

Anything that needs the owner (cost, risk, beyond-MVP) gets both an SCR file here *and*
a matching `OI-<n>` entry in `invai-docs/owner-inbox.md` — the SCR has the full
evidence/cost/risk writeup, the OI entry is the short decidable-in-two-minutes version
that points back to the SCR file. Owner-inbox IDs are a single shared sequence with
`send-owner-draft` entries; get the next one with
`grep -oE "^## OI-[0-9]+" invai-docs/owner-inbox.md | grep -oE "[0-9]+" | sort -n | tail -1`.
