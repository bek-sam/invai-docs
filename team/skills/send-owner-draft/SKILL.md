---
name: send-owner-draft
description: The only path for InvAI outbound text. Any email, reply, post, form answer, marketplace submission, questionnaire, listing or page meant for someone outside the team is written as a draft in invai-docs/owner-inbox.md for the owner to send. Use for "email the shop", "reply to", "submit", "post", "publish", "send to vendor/marketplace/lawyer".
---

# Send owner draft

Nothing leaves the team without the human owner: every outbound message is a complete, reviewed draft in
`invai-docs/owner-inbox.md`, and the agent never sends it.

## When to use
- Any text meant for someone outside the agent team: a shop, pilot, vendor, supplier, marketplace (Etsy,
  Amazon, Shopify, TikTok, Walmart), carrier, lawyer, investor, the public.
- Any form, portal or application answer (app review notes, a security questionnaire, a DPA, a support reply).
- Anything to publish: a web page, a post, an App Store listing, an email sequence, release notes for
  customers.
- Incident notices to shops or Amazon (the 24-hour clocks). Here speed matters: write the draft first, polish
  later.

Not for questions or decisions for the owner. Those use `escalate-to-owner` (same file, same numbering).

## Steps
1. **Write the content where it belongs first.** Long material lives in your owned path, for example
   `invai-docs/compliance/packets/shopify/`, `invai-docs/legal/`, `invai-docs/growth/`,
   `invai-docs/customers/`. The inbox entry links to it and holds the short message itself.
2. **Scrub it.** No real buyer PII, ever (`scrub-pii-fixture`). No secrets, tokens, internal URLs or local
   paths in the text the recipient sees. Shop names only when the owner has already named that shop in the
   task.
3. **Check claims.** Every number, competitor fact or security claim has its source next to it in your working
   file. Public claims, legal text and anything sent to a marketplace get a `compliance-officer` review first
   (operating-system "Who reviews whom"). Security answers also get `security-reviewer`.
4. **Plain language.** Run `write-plain-language-copy`. English first; add Spanish when the recipient reads
   Spanish (floor staff, some shops).
5. **Get the next id:**
   ```
   grep -oE "^## OI-[0-9]+" invai-docs/owner-inbox.md | grep -oE "[0-9]+" | sort -n | tail -1
   ```
   Add 1. Start at `OI-1` if there is none. Drafts share the `OI-` sequence with `escalate-to-owner`.
6. **Append the entry** at the end of `invai-docs/owner-inbox.md`, using [template.md](template.md). Never
   edit or reorder other entries.
7. **Say it in your report:** "Draft queued: OI-<n>, <what>, to <whom>, send by <date>." The task is done when
   the draft is queued, not when it is sent.
8. **When the owner answers,** apply the edits they asked for in your own files and add a new line under the
   entry ("Revised: <date>, <what changed>"). If they sent it, record the send date in your working file (for
   example the packet's status line).

## Rules (MUST / MUST NOT)
- MUST NOT send, post, submit, sign, publish, upload, register, reply, buy or create accounts. No email tools,
  no browser form submits, no API calls to outside services with the text. That includes Gmail, Slack, social
  or marketplace tools, even if they are available in your session.
- MUST NOT put secrets, real PII or raw shop files in the inbox. The inbox is a shared doc.
- MUST NOT write as the owner's personal voice making promises the owner hasn't approved: dates, prices,
  features, legal commitments. Mark each such line `[owner to confirm]`.
- MUST state any clock: the Amazon 24-hour incident notice, the 24-hour shop notice, a marketplace deadline, a
  privacy request due date.
- MUST give a default that is safe when there is no answer: "not sent" is the usual default. Never "sent
  automatically".
- MUST mark legal drafts "DRAFT for counsel" (`legal-doc-draft`) and marketplace packets "not submitted".

## Done when
- The entry exists in `owner-inbox.md` with the next free `OI-` id and every template field filled.
- The full text is in the entry or linked from your owned path, scrubbed and reviewed where the rules above
  require.
- Your report names the entry id and the deadline.

## References
- [template.md](template.md): the entry format
- `invai-docs/owner-inbox.md` (entry format for questions), `invai-docs/team/operating-system.md` ("The human
  owner keeps", "Escalate to the owner")
- Related playbooks: `escalate-to-owner`, `write-plain-language-copy`, `scrub-pii-fixture`, `legal-doc-draft`,
  `incident-response`
