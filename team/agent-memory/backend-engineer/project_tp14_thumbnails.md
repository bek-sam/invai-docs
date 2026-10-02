---
name: project_tp14_thumbnails
description: T-P1-4 (B-209) design thumbnails — grant-scoped client fallback, objectKey's deterministic-id param, cross-module write boundary hit
metadata:
  type: project
---

T-P1-4 (B-209): a client method granted as "the method and its mock only" (no separate mock
provider file) means build the fallback *inline* in that one method — try the real call, catch,
synthesize. `objectKey(companyId, kind, ext, id?)` already takes an optional deterministic `id`
param for exactly this; don't invent a parallel key scheme when a function already supports it
(I didn't use it here only because the yyyy/mm segments would still shift the key across a retry
weeks later, so I wrote a plain `${companyId}/preview/<kind>/<id>.png` helper instead — still
reuse the existing helper when month-drift doesn't matter).

**Why:** `isCompanyKey`-only checks on a client don't stop a corrupted/legacy row; the service that
calls the client must re-check both `file_key` and `out_key` right before every call, even when the
service itself always writes company-prefixed keys today (defense in depth per S-11/S-12 — imaging
doesn't check).

**How to apply:** when a card's AC asks for "fill in later when X completes" and X lives in a
module you don't own/aren't granted, don't write the cross-module update yourself (violates
`modules/<name>never queries another module's tables`). Say so plainly in the report as a gap with
the owning module named, rather than reaching across.
