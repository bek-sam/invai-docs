# 0032: A sheet's print files may be deleted once one of its units is purged; the sheet screens must say why

- Status: accepted (2026-10-09, product-manager)
- Type: product

## Context
Wave 30 card T-30-1 deletes a gang sheet's PNG, PDF and preview once any unit on it has had its buyer text purged (decision 0027 clocks) and the sheet has left production. Reprints are per unit and a purged unit already needs its text re-entered to re-render (0027 "Re-entry"), so a reprint never reuses the old sheet file; it builds a new sheet. The sheet row, transfers, counts, cost and dates stay. The web disables the PNG/PDF download buttons when a key is null (`sheets.$sheetId.tsx:204`) with no explanation, so a shop may think the app is broken. Evidence: Amazon DPP "PII deleted 30 days after delivery" row, backlog B-300; no pilot has asked to re-download a sheet older than 30 days after delivery (none logged in `customers/`).

## Decision
1. Deleting a sheet's files after a purged unit is acceptable, only for sheets in `printed`, `shipped`, `received`, `cancelled` or `failed` (T-30-1 AC2-AC3). Sheets still `building` through `acknowledged` keep their files.
2. A disabled download button with no reason is not acceptable as the final state. Ship T-30-1 as is (no web change in that card), but the web must show a plain-language line next to the disabled buttons on both the shop and the vendor sheet screen: EN "Print files were removed to protect buyer data, 30 days after delivery." ES "Los archivos de impresion se quitaron para proteger los datos del comprador, 30 dias despues de la entrega." Copy to be finalised by write-plain-language-copy.
3. Follow-up row for the tech lead to add to the backlog: web-engineer, P2, sheet screens (shop and vendor) explain removed files; target wave 31 (before any pilot shop's first 30-day purge, which cannot occur before pilots deliver orders). Needs no contract change if `files` keys null is enough; if the architect wants an explicit `filesPurged` flag, it is a separate contract card.
4. No re-render of sheets without the text (out of scope in T-30-1): the shop never gets a text-free copy.

## Consequences
- A shop cannot re-download an old sheet after the clock; a sheet needed again is rebuilt from units (re-entering text for purged ones).
- Revisit if two pilot shops report needing old sheet files, with a retention option that the compliance-officer must approve.
