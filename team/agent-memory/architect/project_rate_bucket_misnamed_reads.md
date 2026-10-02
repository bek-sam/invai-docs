---
name: project_rate_bucket_misnamed_reads
description: Contract procedures named *.read but that actually write (alerts, today, digest, market.vote) — checklist for any rate-bucket or permission-audit card
metadata:
  type: project
---

For T-P3-1 (B-236, wave P3, 2026-09-30 plan review): the contract has ~12 non-GET procedures whose
permission ends in `.read` but whose handler writes or spends — `alerts.markRead`/`markAllRead`,
`orders.addNote`, `digest.feedback`/`recordClick`, `market.recommendations.vote`,
`tenancy.org.set`, `tenancy.today.start/reset/leave`, `today.dismissChecklist`/`recordActionClick`,
`analytics.export` (writes a CSV to storage), `finance.exportCsv` (returns `JobRef`),
`personalization.preview` (calls the imaging render — outbound/costly).
**Why:** permission name alone is not a safe signal for rate-bucket classification (or any future
read/write audit) — the handler must be read. `inventory.stock` and `shipping.batchLabelPdf` are
POST only because of body size, with no side effect, so they're good `reads`-bucket candidates
alongside `files.downloadUrl`.
**How to apply:** any card that classifies procedures by read/write intent (rate limits, audit
logs, caching) should walk the full list above by hand, not grep `.read`/`.manage` in the
permission string. See [[feedback_contract_version_bump_convention]] for the related "don't trust
the name, read the handler" pattern on enum/version bumps.
