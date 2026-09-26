# T-9-2: Sheet barcode, scannable QRs, label gap (B-79)
Evidence: §A-INF B-4, B-5, B-11 (`compose.py:26,76-88,188`, random object keys in `sheets.ts:559-561`).
## Acceptance criteria
1. **Label QRs:** transfer label QRs are always rendered at 300 DPI or more, whatever the sheet DPI, with a minimum module size of at least 0.5 mm. If they can't fit, compose fails loudly.
2. **Sheet header:** a header barcode or QR with the sheet id. The file name includes the sheet id and order numbers, which RIP job lookup needs (CADlink).
3. **Label gap:** configurable in the sheet spec, default 0.125 in, with a thin cut guide.
4. **Tests:** decode the QRs from composed sheets at 150, 200 and 300 DPI with a decoder in tests, and check the header decodes.

## Plan review r1 — files, sequencing, gap
Runs in the **3-way parallel batch** (see `wave.md` §Plan review r1), after T-9-1 lands.

**Owns:** `app/compose.py` (QR module size/DPI floor, header barcode, label gap — plus the one-line `load(src, target_dpi=...)` call in `_prepare_design` once T-9-1's `vips.py` change is in), `app/storage.py` (add an optional `download_filename` param to `upload()` that sets S3 `ContentDisposition`). **Narrow grants only:** `app/main.py`'s `ComposeRequest` class (add `label_gap_in`, `filename_hint`) and `invai-contracts/src/schemas/vendors.ts`'s `SheetSpec` (`labelGapIn`) — touch only those, not the rest of either file.

**AC2 scope gap:** the audit's "random object keys" evidence is `invai-backend/src/lib/s3.ts:559-561` (`sheets.ts`), which is outside invai-imaging and deliberately keeps S3 keys opaque (`objectKey`'s own comment: "keys never contain user input") — don't change that file or that invariant. Satisfy "file name includes the sheet id and order numbers" by setting `ContentDisposition: attachment; filename="..."` on the compose upload instead, driven by the new `filename_hint` field. That's a download-time filename, not the S3 key, which is what a vendor/RIP operator actually sees when saving the file.

**AC1 testability:** "compose fails loudly" needs a precise trigger — define the minimum label-strip height (in) below which a 0.5mm-module QR can't be laid out at the sheet's DPI, and assert `ImageError` exactly at that boundary, not just "somewhere small."
