# Review: T-21-1 Legal drafts for counsel — product-manager (domain), round 1

Reviewer: product-manager  Verdict: **changes-required** (one small fix, everything else approved)

## Scope

Verified against `product/scope.md` (MVP in items 1–17, segments, fences on 16/17) and
`decisions/0006-v1-cuts.md`. `terms.md` §2 describes only what's shipped or explicitly marked pending
(order import → gang sheets → scan-checked floor → labels → profit → AI listing drafts with human approval →
vendor portal); §4 correctly states Shopify is live API/webhook while Etsy/Amazon/TikTok/Walmart are CSV
import pending each marketplace's app review, matching decision 0006. No mention of a feature that doesn't
exist and no product claim beyond scope.

## No promise the product doesn't keep

- **Auto listing/price changes:** `terms.md` §5 — AI drafts are never published without human approval,
  cited to `invai-backend/src/modules/ai/service.ts:58,633`. I checked both lines directly: line 58 is the
  "nothing is published without human approval" comment, line 633 is the `approvedBy` write. Consistent with
  the scope fence "No automatic price or listing changes."
- **AI summary shadow mode (item 17):** not claimed anywhere as live. `subprocessors.md`'s email row and
  `dpa.md`'s nature/purpose section only describe the human-authored digest and listing-draft AI paths; the
  `digest_narrative` shadow route isn't mentioned, which is correct — it never sends anything today, so
  silence here doesn't overstate it. No false claim.
- **Email opt-in:** `subprocessors.md` states "opt-in weekly digest email" with a cite to
  `specs/weekly-digest.md` §"Delivery"; `privacy.md` doesn't claim any non-opt-in marketing email. Correct.
- **Plan limits / prices:** `terms.md` §7 is fully `[[OWNER: ...]]`, states billing is stubbed today
  (`invai-backend/src/env.ts` `mocks.billing`), and explicitly says no Shop is charged before that section is
  filled in. No invented dollar figure anywhere in the 8 files (`grep -n "\$1\|\$3\|\$6\|per month" legal/**`
  found nothing but the placeholder text itself).

## Facts checked against code (spot check, independent of the report's own table)

I re-read the cited lines myself rather than trusting the report:
- `PII_RETENTION_DAYS = 30` — `invai-backend/src/modules/orders/jobs.ts:13` ✓
- `BUYER_PII_RETENTION_MONTHS = 18`, `HARD_PURGE_DELAY_MS = 30 * 86400_000` —
  `invai-backend/src/modules/privacy/service.ts:283,285` ✓
- `stripPii`/`stripPiiDeep` scrub email, phone, address, zip, card-like numbers —
  `invai-backend/src/ai/pii.ts:1-24` ✓, matches `privacy.md` §4's claim exactly (no over- or under-claim)
- Shopify's three GDPR compliance webhooks — `invai-backend/src/integrations/channels/shopify/common.ts:263-267`,
  `invai-backend/src/modules/privacy/service.ts:55-65` ✓
All match the drafts' claims. No overstated or invented fact found.

## Placeholders and banner

- `grep -c "DRAFT for counsel review. Not in force." legal -r` → 1 per file × 8 files ✓
- `grep -c "\[\[OWNER\|\[COUNSEL" legal/*.md legal/es/*.md` → 11–17 per file, none of the Spanish files have
  fewer placeholders than their English counterpart (dpa 11/11, privacy 13/13, subprocessors 13/13,
  terms 17/17) — the translator didn't quietly fill in a placeholder. ✓
- No invented AWS region, RDS backup window, or email provider — each is an explicit `[[OWNER: ...]]`, even
  though `S3_REGION`'s code default is `us-east-1` (correctly flagged as a default, not a confirmed
  production fact).

## Spanish

All 4 Spanish files are complete translations (line counts 134–160 vs. English 58–143, longer as expected
for Spanish), each opens with the same "BORRADOR..." banner and "la versión en inglés es la que cuenta"
note, and carries the same placeholder count as its English source (checked above). Read `es/privacy.md` and
`es/subprocessors.md` in full: natural Spanish, glossary-consistent role names
(dueño/administrador/oficina/diseñador/prensista/empacador/receptor), no truncation or leftover English
sentence.

## Plain language / no forbidden claims

`grep -inE "secure|compliant|guarantee|garantiz"` across all 8 files returns only disclaiming uses ("cannot
guarantee a marketplace's uptime", "not... a guarantee of non-infringement", "no puede garantizar") — these
negate a guarantee, they don't make one. No "secure/compliant/guaranteed" marketing claim found.

**One real defect:** `legal/dpa.md` §8 (English), line 97:
> "...delete it within 30 days of a deletion request (sooner if the Controller cancels during the
> export-only window is not offered; the export and the deletion clock run together)."

This sentence doesn't parse — it reads as two edited clauses merged into one ungrammatical parenthetical.
The Spanish translation at `legal/es/dpa.md` lines 108–109 is actually correct and clear ("no se ofrece un
plazo de solo-exportación por separado; la exportación y el plazo de eliminación corren juntos" = "no
separate export-only window is offered; export and deletion run together"), so the intended meaning is
right and the fact is accurate — this is a copy defect in the English source, not a wrong claim. Fix
requested: rewrite the English parenthetical to match the Spanish's sense, e.g. "(no separate export-only
window is offered; export and deletion run on the same clock)."

## OI-19 (counsel timing)

Read in full. One question, three real options (A engage now / B wait for DPP+email gaps / C wait for a
paying shop), a stated recommendation with reasoning, context that names the concrete evidence file
(`waves/21/reports/T-21-1.md`), and an honest list of what's still open (no MFA, no centralized log, KMS
key unused, no email provider, no RDS backup figure, no error-tracking vendor) so the owner isn't surprised
later. Reads well and is decidable in under two minutes.

One nit, not blocking: the "Deadline" field is event-conditioned ("before InvAI signs its first paying shop
or connects a live [...] app") rather than a calendar date/time as `escalate-to-owner`'s own template
prescribes (`YYYY-MM-DD HH:MM TZ`). Given "Cost of waiting" already states this blocks nothing else in
waves 21–22, I don't think it's worth a second round over — the owner can still act whenever suits them — but
flagging so a future OI on a faster-moving topic doesn't copy this pattern where a real clock is needed.

## Verdict

**changes-required**, scoped to one fix: correct the garbled sentence in `legal/dpa.md` §8 (English). Every
acceptance criterion (1–5) is otherwise met with verifiable evidence; no promise the product doesn't keep, no
invented price or plan detail, Spanish complete and glossary-consistent, plain language holds, and the
"DRAFT for counsel review. Not in force." banner is on all 8 documents. Once §8 is fixed, this is a clean
approve from me — no second full pass needed, a diff of that one paragraph is enough.
