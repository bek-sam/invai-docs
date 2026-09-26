# T-8-4: Trademark-risk gate (B-46)

Owned files (wave.md "File ownership and batches", batch 2, runs after T-8-1 lands): `src/modules/ai/trademark.ts`; the gate checks inside `approveDraft`, `publishDraft`, `exportListingsCsv`, `trademarkCheck` in `src/modules/ai/service.ts`; the `invai-ui`/`invai-web` files, outside this split.

## Acceptance criteria
1. **Blocked range:** a trademark risk score of 60 or more blocks publishing and export of the draft, unconditionally — no override, including the current `acknowledgeRisk` bypass in `approveDraft`, which this card removes. The web shows why and which marks matched.
2. **Review range:** a score of 25–59 needs a recorded human review (who, when, a note) before publishing. Design exactly per wave.md "Contract stubs / A": the `trademarkReview` column set, the `recordTrademarkReview` procedure, and the `TRADEMARK_REVIEW_REQUIRED` error. Stored on the draft and in the audit log.
3. **Low range:** a score under 25 has no gate.
4. **Enforcement:** the gate is enforced in the backend (`approveDraft`, `publishDraft`, `exportListingsCsv`), not only in the UI, and re-checks the draft's **current** `trademark` field on every call rather than trusting a value cached at approval time.
5. **Quality:** en and es. Tests for each range (< 25 publishes clean; 25–59 blocks until `recordTrademarkReview`, then publishes; >= 60 blocks even after a review is recorded).
