---
name: imaging-key-trust-model
description: invai-imaging's Key field is pure length validation, no company-prefix check anywhere; isCompanyKey() enforcement lives only in the backend.
metadata:
  type: project
---

`invai-imaging/app/main.py`'s `Key = Field(min_length=1, max_length=512)` is used for every
`*_key` input (`file_key`, `out_key`, `background_key`, etc.) across every route, including the
new `POST /preview` (T-P1-2). It never checks a company prefix. Verified live (2026-09-30,
T-P1-2 review): a `/preview` call with `file_key` under `companyA/` and `out_key` under
`companyB/` succeeds and writes into `companyB`'s prefix — imaging will happily cross tenants if
asked to.

**Why this is accepted, not a bug:** `invai-docs/security/v1-review.md` S-11/S-12 already
establish that the enforcement point is the **backend**'s `isCompanyKey()` check
(`invai-backend/src/lib/s3.ts`), called before the backend ever invokes imaging — imaging trusts
the caller completely, by design (`CLAUDE.md` / role brief: "Imaging trusts the backend to pass
company-prefixed keys").

**How to apply:** when reviewing any imaging card with the `files` flag, don't expect or demand a
company-prefix check inside `invai-imaging` itself — that would be the wrong layer. Instead check
that whichever backend card wires a new imaging endpoint to a contract procedure
(e.g. T-P1-4 for `/preview`) adds `isCompanyKey()` on *every* `*_key` field the backend passes
through, both inputs and outputs (`out_key` too — it's a write key, forgetting it lets a
compromised/buggy caller overwrite another tenant's object). Flag this explicitly as a required
acceptance criterion on that backend card rather than blocking the imaging card.

See also [[imaging-guard-middleware-deny-by-default]].

**T-P1-4 follow-up (2026-09-30):** the request/job path (`catalog.renderDesignPreviews` ->
`service.ts`'s `renderDesignPreviews()`) does call `isCompanyKey()` on both `file_key` and
`out_key` before every `imaging.preview`, as required. But `src/db/seed/builder.ts` calls
`imaging.preview` **directly**, bypassing that service function and its check entirely. I judged
this not exploitable only because the seed builds both keys from its own trusted `shopId` (not
request input) and `fileKey` was already `isCompanyKey`-validated moments earlier by
`createDesign()`. Next review: grep every caller of `imaging.<method>` (`grep -rn "imaging\."
src/db/seed src/modules`), not just the job/service path — seed and backfill scripts are an easy
place to lose the check when they call the integrations client directly instead of going through
the checked service function.
