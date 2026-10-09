# Review: T-29-1 compliance co-review r1
Reviewer: compliance-officer (read-only on code; test and control facts taken from the reviewer's r1 re-run and the author's report). Security co-review not yet in the folder.

## Verdict: approve. Compliance accepted in decision 0027 (2026-10-09); status stays "proposed" until security-reviewer accepts.

## Does 0027 match DPP and my wave 28 answer? Yes
- PII: 30 days after delivery; no delivery event -> 30 days after `shipped_at`; matches the DPP row and S-16. Personalization answers, `item_artwork` values, rendered art and buyer photos, and free-text notes are all on that clock, as I said (T-28-3 answer, scope plus the note finding 1).
- Non-PII / everything: 18 months after `placed_at`, every channel, scope `all`. Matches the DPP row and 0026.
- Per-unit clock (other units keep art while in production) is correct: the 30 days run from delivery, the reprint window stays open.
- Keep list is order facts only (ids, SKUs, amounts, dates, enums); machine/sheet notes are not buyer text. Fine.
- Cancelled orders at `cancelled_at`: OK. DPP says "after delivery", a cancelled order has none; same stricter rule already accepted in S-16. Not a deviation to disclose, a conservative choice.
- Refund-note narrowing of 0026: consistent. OI-19 (owner-inbox line 204) carries the tech lead's note that 0027 narrows the keep list; counsel asks about titles only. Narrowing is the safer direction, so no new inbox entry.

## Known gaps: honest, owned, but they decide the Amazon packet
| Gap | Owner | Blocks Amazon restricted-role application? |
|---|---|---|
| Gang sheet print files/previews hold rendered buyer text (`PII_OBJECT_KINDS` = raw,csv,label) | backend-engineer (production), P1 with B-293 | YES. Buyer-identifying data older than 30 days; the "PII deleted 30 days after delivery" row cannot be marked closed until fixed |
| Renders superseded before T-29-1 (orphans) | backend-engineer (personalization), one-off sweep | YES (small). Same row; do the sweep before the application or list it as open with a date |
| `audit_log` `artwork.rendered` `data.flags` quote values; append-only | security-reviewer + backend-foundation | Evidence-pack open item with owner/date. Fix at source (stop writing values) plus a documented redaction path; if neither exists at application time, disclose as Partial, not closed |
| Manual-override art outside `{company}/artwork/` or shared by items: keys nulled, object kept | not in 0027; only in the author's report | Open item in the pack. Needs an owner (backend-engineer personalization) |

## Findings (non-blocking)
1. 0027 "Known gaps" omits the manual-upload case that the report states. Add it with owner (tech lead to ask author; I did not edit their text).
2. DPP 30-day row and 18-month row stay **Partial** in the evidence pack and `security/v1-review.md` until the first two gaps close and counsel answers OI-19. Do not mark closed.
3. Reviewer note 2 (render deleted before photo leaves an approved unit with a dead key until next run) is acceptable; self-heals nightly.
4. Retention claims in the privacy policy/DPA drafts that say "personalization text purged at 30 days" are true for rows only once this is pushed, and not for gang-sheet files until the P1 lands. I will word the drafts accordingly.

## Actions I take
- Evidence pack: add the four gaps as open items with owners (next compliance pass).
- Deadline for the Medium S-56: 2026-11-08; the gang-sheet gap should land by then too.
