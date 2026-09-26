# T-9-3: Long PDFs without `/UserUnit` (B-80)
Evidence: §A-INF B-3 (`app/pdf.py:43-47`).
## Acceptance criteria
1. **Long sheets:** sheets over 200 in must not rely on `/UserUnit`. Either split into pages of 200 in or less with alignment marks, or cap `max_length_in` for PDF output at 200 with a clear validation error at spec save. Choose one, record the decision, and apply it to both the contract bounds and imaging.
2. **Tests:** a 240 in sheet is either split correctly (with page count and size checked) or rejected with the error.

## Plan review r1 — decision, files, sequencing
Runs in the **3-way parallel batch** (see `wave.md` §Plan review r1), after T-9-1 lands. No dependency on T-9-1/T-9-2/T-9-4's changes — disjoint files.

**Decision: cap, not split.** Cap `maxLengthIn` at 200in for `format: "pdf"` only (PNG has no page-size/`/UserUnit` concept, so it keeps the current 240in ceiling — B-80 is a PDF-only bug). Splitting into ≤200in pages with alignment marks would roughly double this file's surface (page layout, registration marks, re-assembly tests) for a case that's rare at the segment this wave targets — `scope.md` pilots start at **mid**, with **large** shops (most likely to run >200in) gated behind `scale-test`. CADlink and comparable RIPs expect one continuous image per barcode/job lookup, so a multi-page PDF pushes re-assembly work onto the press, a worse outcome for self-serve/assisted shops than a cap. 200in × 72pt = 14,400pt is exactly the existing `MAX_PAGE_PT`, so capping removes the `/UserUnit` branch entirely rather than special-casing it.

**Owns:** `app/pdf.py` (drop/guard the `/UserUnit` branch, raise `ImageError` above 200in for PDF output). **Narrow grants only:** `app/main.py`'s `max_length_in` bound on `NestRequest`/`ComposeRequest` (don't touch other fields/classes) and `invai-contracts/src/schemas/vendors.ts`'s `SheetSpec` — add the `.refine` below.

**Enforce at spec save, not just compose:** a vendor shouldn't be able to save a >200in PDF spec at all.
```ts
.refine(
  (s) => s.format !== "pdf" || s.maxLengthIn <= 200,
  { message: "PDF sheets are capped at 200in; use PNG for longer runs.", path: ["maxLengthIn"] },
)
```
Keep `app/pdf.py`'s own `ImageError` as a second line of defense in case something bypasses contract validation.
