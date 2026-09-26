# Review of T-7-1 (round 1)

- Reviewer: compliance-officer on Sonnet 5
- Author: integrations-engineer + web-engineer on Sonnet 5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `invai-backend` worktree @`24b6790`: `tsc --noEmit`, `biome check .`, full `vitest run` | 1 failed / 525 (`export-tracking.test.ts:111`, re-export) — see reviewer's file for the full trace and root cause |
| Read `integrations/channels/exports/tracking.ts` in full, cross-checked each marketplace's cited source against the column names/carrier codes actually emitted | see below |
| Live DB-copy export + download (Etsy, `:3194`/`:5194`, `owner@desertbloom.test`) and a repeat call | file downloaded and inspected; repeat call re-exported a shipment that had already been exported (`count:1` instead of `0`) |

## Acceptance criteria (compliance-relevant slice)
| # | Met? | Evidence |
|---|---|---|
| 1. Each file matches the marketplace's own current format, carrier code mapping per marketplace | Yes, with the sourcing caveat below | Etsy fields match Open API v3 `createReceiptShipment` (cited, dated 2026-09-25); Amazon's tab-delimited columns match the documented `POST_FLAT_FILE_FULFILLMENT_DATA` feed and the carrier-code/ship-method requirement Amazon made mandatory 2021-04-15 (cited, cross-checked against 2 sources); TikTok and Walmart columns are the best public-source approximation since their live templates sit behind a Seller Center login (disclosed by the author, not hidden) |
| 2. `exported_at` re-export | **No** — marketplace-policy risk, see blocking finding |

## Blocking findings
1. Same root cause as the reviewer's finding 1 (`service.ts`, DB-clock vs. app-clock cutoff mismatch) has a marketplace-policy angle worth calling out on its own: an unintended re-export means the **same tracking number can be resubmitted to a marketplace's bulk-upload channel more than once** without the merchant asking for it. For Etsy specifically, tracking updates go through `createReceiptShipment`/a connector built on it — a duplicate call isn't dangerous by itself (Etsy treats a repeat tracking-add as a no-op or an update), but it does mean this feature cannot yet make the claim in its own UI copy ("tracking uploaded (manual)" / "nothing new to export") that the export state is trustworthy. A merchant who re-runs the export "just to be safe" (a very likely real-world action, since nothing today tells them their last export succeeded on Etsy's side) gets a second file with the same rows, may re-upload it into a third-party bulk connector, and could trip that connector's own duplicate/rate-limit handling. This must be fixed before the export can be represented to shop owners as a reliable "last export" boundary — approve blocked on the same fix the reviewer specifies.
2. No PII- or over-disclosure concerns found in the file contents themselves: Etsy's file carries `receipt_id`/`tracking_code`/`carrier_name` only (no buyer name/address); Amazon's carries `order-id`/`order-item-id`/quantity/dates/carrier/tracking only; same for TikTok/Walmart. This is not a blocking finding — noted for the record since it was in scope for this pass.

## Checks
- [x] Only owned paths changed.
- [x] Nothing outside scope; no Etsy AI-disclosure, `production_partner_ids`, trademark, or synthetic-performer surfaces are touched by this card (those apply to listings, not tracking export) — correctly out of scope.
- [x] Carrier code mapping is exhaustive and correct per marketplace for the 3 carriers the platform supports (`usps`/`ups`/`mock`), each mapped to that marketplace's documented accepted value (Amazon: `USPS`/`UPS`/`Other` with `carrier-name` only filled for `Other`, matching Amazon's own conditional rule; Walmart: exact names from the supported-carrier-names list, `Other` + tracking URL for anything outside it, matching Walmart's own fallback rule).
- [x] CSV/TSV formula-injection guard (`neutralizeFormula`) is applied on every emitted field and is unit-tested — this matters for compliance since these files get opened in Excel/Sheets by shop owners before upload.
- [x] The query never crosses channel boundaries: verified the `orders.channel = input.channel` join plus the `isTrackingExportChannel` gate keeps Shopify orders and any hypothetical `pushed` status out of a CSV-channel's export — no mixing of marketplace data across files.
- [ ] Idempotency (webhooks/labels/tracking pushes) — blocking, see above.

## Optional notes (not blocking)
- Recommend the report's own follow-up stand: have the first real shop diff the Etsy/TikTok/Walmart file against each marketplace's live Seller Center template once real credentials exist, since those three templates aren't publicly downloadable today.
- No trademark, restricted-content, or synthetic-media concerns apply to a tracking-number export; scope of this card doesn't touch listing content.
