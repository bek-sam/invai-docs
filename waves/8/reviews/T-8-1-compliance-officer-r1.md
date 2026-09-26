# Review of T-8-1 (round 1)

- Reviewer: compliance-officer on Sonnet 5
- Author: ai-engineer on Sonnet 5
- Verdict: approve

Co-review per `listing-compliance-check`, alongside the primary reviewer's `independent-review` pass
(same evidence run once; this file records the compliance-specific read).

## Evidence I re-ran
| Command | Result |
|---|---|
| Live fetch `https://www.etsy.com/legal/creativity` | 403 (matches the author's claim that etsy.com blocks automated fetches) |
| `curl http://archive.org/wayback/available?url=etsy.com/legal/creativity` | Confirms `20260828105429` is Wayback's closest snapshot to today (2026-09-26) — the exact one cited in code |
| Live fetch of that Wayback snapshot, extracted the "designed by a seller" section | Verbatim: "Sellers must disclose within their listing description if an item is created with the use of AI." and "Sellers must disclose that an item is made by a production partner, and provide accurate information about where the item will ship from." |
| Diffed `AI_DISCLOSURE`/`PARTNER_DISCLOSURE` (`invai-backend/src/ai/validators/listing.ts`) against that wording | AI disclosure: accurate paraphrase, frames the design/seller-prompted, never claims the finished product is AI-made — passes the rule "MUST treat Etsy's AI disclosure as being about the item or design" |
| `grep -n "PARTNER_DISCLOSURE\|AI_DISCLOSURE\|printsInHouse\|withDisclosures" src/modules/ai/service.ts src/ai/validators/listing.ts` | `withDisclosures` still appends both strings unconditionally on every channel/every listing — unchanged trigger logic |
| `pnpm test` (backend, own DB) + read of `service.test.ts`/`ai.test.ts` new cases | production_partner_required, all-caps, repeated-phrase cases all present and pass; CSV export test confirms `production_partner_ids` is blank until an Etsy partner id is set, then round-trips |
| `grep -rniE "buyer.*email|buyerEmail|sendMail|sendEmail|mailer" src/ai/** src/modules/ai/**` | empty (no buyer email path) |

## Per-channel checks (rules.md, Etsy section)
| Check | Result | Evidence | Rule source |
|---|---|---|---|
| AI disclosure is about the design, in the description, never "AI-made product" | pass | `AI_DISCLOSURE` reworded; matches live-verified policy text; disclosures array is appended into the listing description via `withDisclosures` | etsy.com/legal/creativity (verified live+Wayback this review) |
| Production partner uses the structured field, not just a sentence | pass | `production_partner_ids` column added to the Etsy CSV branch (`c.productionPartner ?? ""` for the name column, `etsyPartnerId ?? ""` for the ids column); `production_partner_required` blocks generation without one configured | research 10 §3; wave.md Contract stubs / C |
| In-house shops not falsely described as using a partner | **warn** (pre-existing, not fixed by this card) | `PARTNER_DISCLOSURE` is still appended unconditionally by `withDisclosures` regardless of `companies.settings.printsInHouse` — the exact M-23 gap rules.md already tracks. This card only reworded the string's text; it did not touch the trigger. Fix owner: ai-engineer, follow-up card (not blocking T-8-1, which never claimed to fix this) | rules.md M-23 |
| Title length 140 max | pass (pre-existing, unchanged) | `title_max_140` via `CHANNEL_RULES.etsy.listing.titleMax` | contracts `channels.ts` |
| Title all-caps | pass, judgment call documented | New Etsy-only `title_all_caps`, threshold = 0 all-caps words of 4+ letters (acronyms/sizes ≤3 letters exempt). Etsy's own Seller Handbook language ("looks spammy") has no numeric cap, so zero-tolerance is a defensible reading, not an invented number — verified via the same Wayback-cited source class the author used. Flagging as a judgment call the PM/architect should confirm doesn't over-block legitimate titles (e.g. "MADE" in "MADE TO ORDER" would now trip it) | Seller Handbook "New Guidance for Listing Titles" (author's Wayback snapshot 2025-12-02) |
| No 3+-word repeated phrase | pass | `title_repeated_phrase`, 3-gram check, case/punctuation-insensitive, catches any longer repeat too | same Seller Handbook source |
| Trademark risk ≥25 shows a notice | N/A for this card | Correctly deferred to T-8-4 per wave.md's file ownership; nothing here regresses the existing (pre-T-8-4) state | team rule, `combineRisk` |
| No buyer email anywhere in AI/listing flows | pass | grep confirmed empty | R15/agent-brief |
| No training on marketplace data | pass (unaffected) | This card doesn't touch model training/tuning paths | research 10 R15 |
| Human approval before publish | pass (unaffected) | `approveDraft`/`publishDraft` flow untouched by this card | Amazon BSA Agent Policy; team rule |

## Trademark threshold
Out of scope for T-8-1 (owned by T-8-4, which lands after this card per wave.md's sequencing). No gate logic was added or changed here; confirmed by diff review — `trademark.ts` and the `approveDraft`/`publishDraft`/`exportListingsCsv` gate checks are untouched in commit `bb075e8`.

## Verdict
**Approve.** All of this card's compliance-relevant acceptance criteria (AI disclosure wording, `production_partner_ids`, title rules, no buyer email) are met and independently verified against Etsy's live/Wayback-snapshotted policy text. Two pre-existing gaps are surfaced as non-blocking follow-ups, neither introduced or worsened by this card:
1. `PARTNER_DISCLOSURE` still doesn't gate on `printsInHouse` (M-23) and still omits the ship-from-location clause Etsy's policy also asks for.
2. `AI_DISCLOSURE` still fires unconditionally regardless of whether the design was actually AI-made (over-disclosure, not under-disclosure — lower risk, but still inaccurate copy in a legal-disclosure field).

Route both to ai-engineer as a follow-up card; neither blocks this one since the card's stated ACs are about wording accuracy and the `production_partner_ids` plumbing, both of which are correct.
