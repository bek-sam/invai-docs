# Review of T-8-4 (round 1)

- Reviewer: compliance-officer on sonnet
- Author: ai-engineer + web-engineer on sonnet
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend diff a32b682 f3b0eea -- src/modules/ai/trademark.ts src/modules/ai/service.ts` | read in full |
| `git -C invai-web diff 5c6ab28 98a47a9 -- src/routes/_app/listings/drafts.\$draftId.tsx` | read in full |
| `git -C invai-backend diff a32b682 f3b0eea -- src/modules/ai/service.test.ts` | read in full, cross-checked against the trademark gate ranges |
| Real-DB audit-row check per the report (`data: {riskScore: 40, note: "..."}` on `listing_draft.trademark_review`) | reproduced independently by re-running `service.test.ts`'s "25-59 blocks until recordTrademarkReview, then publishes" case (see reviewer's file); matches the required audit shape |
| `grep -rn "acknowledgeRisk" invai-backend/src invai-web/src invai-contracts/src` | confirms no functional bypass remains anywhere |

## Acceptance criteria (compliance lens — `listing-compliance-check` §"Trademark threshold")
| # | Met? | Evidence |
|---|---|---|
| `high` (>=60): never publish as-is, no override | Yes | `assertTrademarkGate` throws `HIGH_TRADEMARK_RISK` unconditionally, called live at approve, publish and export — three separate enforcement points, one function, so the three can't drift. The former `acknowledgeRisk` override in `approveDraft` is deleted, not just hidden; `grep` across all three repos found it only in a deprecated, unread contract input field and in comments explaining its removal. |
| `medium` (25-59): human review recorded with the draft, before publish | Yes | `recordTrademarkReview` requires `riskLevel === "medium"`, stores `reviewedBy`/`reviewedAt`/`note` on the draft (`trademarkReview` on `ListingDraft`), and writes an audit row `listing_draft.trademark_review` with `{riskScore, note}` — the reason is kept with the draft, not just logged. `note` has a real min-length check (3 chars) enforced at the contract layer (`z.string().min(3)`), not left to client discipline. |
| `low` (<25): publish allowed after normal approval | Yes | No gate triggers; the normal human-approval step (`approveDraft`) still applies. |
| Re-checked live, not cached | Yes | Confirmed by the reviewer's re-run of the "risk moved after approval" test: an approved-at-low-risk draft that is later mutated to high still blocks at both `publishDraft` and `exportListingsCsv`. This matters for compliance specifically because a shop could otherwise get a draft approved while clean and publish it after new marks were indexed, or after a human edit reintroduced a flagged phrase without re-triggering the trigram check. |
| UI states the check is a risk score, not legal advice | Yes, unchanged | The disclaimer lives in `trademark.ts`'s `explain()` (untouched by this diff) and is still rendered in the `TrademarkResult` panel on the draft page. The new banner text (`trademarkNoticeHigh`/`Medium`/`Reviewed`) is additional and doesn't repeat or contradict that disclaimer; it sits next to the panel that carries it, which was this card's job (closing T-8-1's AC4, per wave.md). |
| Human approval retained on every publish path | Yes | `approveDraft` is unchanged as the required gate before `publishDraft`; nothing in this diff lets a draft skip approval. |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope — no changes to `CHANNEL_RULES`, Etsy disclosure text, or `production_partner_ids` (T-8-1's area); this card correctly stayed inside the trademark gate
- [x] Tests exercise the behavior, and none were weakened — the pre-existing high-risk approval test was strengthened (blocked on repeated attempts, only clears once the flagged text is actually edited away), matching the "no override" rule more strictly than before
- [x] The reason for a medium-risk review is kept with the draft (`trademarkReview.note`), not only in the audit log
- [x] No legal-advice language was added; the existing risk-score disclaimer is untouched

## Optional notes (not blocking)
- `recordTrademarkReview` doesn't check the draft's workflow status, only its risk level — per wave.md this is intentional (a compliance reviewer can sign off ahead of an approval attempt). Worth a lesson entry if a future card wants review timestamps tied to a specific draft version, since an edit after the review doesn't invalidate a still-medium score's existing review.
