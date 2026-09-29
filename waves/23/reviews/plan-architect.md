# Wave 23 plan review — architect

**Verdict: approve**

Only `wave.md` exists for wave 23 (no individual `T-23-*.md` cards yet), so this is a design review
of the wave-plan level, same as PM's.

## Checked
- Every wave-23 capability is a consumer of something wave 22 builds (screens for T-22-1's new
  procedures, floor for T-22-4's maintenance/QC-reason/bin fields) — correct "no dead procedures"
  sequencing, and correctly gated on wave 22's push (T-23-1/T-23-2 wait for it; T-23-3/4/5 can start
  earlier since they don't depend on wave 22's contract additions).
- PM's required change (the B-131 seasonality-formula fix belongs in `specs/market-signals.md`,
  written by product-manager, not granted to an engineer) is a product/spec-ownership call, not a
  contract one — I have no addition there. Agree it should land in the T-23-4 card as written.
- No card in this wave proposes a new contract procedure or field outside what T-22-1 already
  planned, so there's no contract-first-order violation to check here yet.

## Notes (non-blocking, for when the individual cards are written)
- T-23-1's buyer-photo upload (B-81 rest): the contract already supports a photo personalization
  slot (`kind: z.enum(["text", "photo"])` and `low_res_photo` in
  `invai-contracts/src/schemas/personalization.ts`, from wave 9's T-9-4). What's open is the
  template-editor upload UI. When the card is written, confirm it can use the existing generic file
  upload path (`invai-contracts/src/contract/files.ts`) rather than needing a new contract shape; if
  it does need one, that's an architect card first, per the change order.
- T-23-2's camera scanner (B-105 rest) should just feed the same string a keyboard-wedge scan
  produces into the existing `ScanInput.transferCode`/`blankCode` — no contract change expected;
  flag it to me if the camera path needs something the string-based scan doesn't have (e.g. a
  confidence score) before the card is written.
