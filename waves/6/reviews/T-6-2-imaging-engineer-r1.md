# Review of T-6-2 (round 1) — imaging-engineer co-review (labels endpoint)

- Reviewer: imaging-engineer on Sonnet 5
- Author: (unattributed in report) on sonnet
- Verdict: **approve**

Scope of this co-review: `invai-imaging`'s new `POST /labels/qr` endpoint (`a773566`, `896163a`)
— input bounds, rendering correctness, and whether it's safe to expose to backend callers. Full
cross-repo evidence (tsc/lint/test/build elsewhere, the DB-copy pass, scan-test-weakening) is in
`T-6-2-reviewer-r1.md`; this file re-runs only the imaging-specific checks plus its own targeted
input-bounds read.

## Evidence I re-ran
| Command | Result |
|---|---|
| `invai-imaging` (already at HEAD `896163a`, no worktree needed): `uv run ruff check .` | all checks passed |
| `invai-imaging`: `uv run pytest` | 30 passed, including `tests/test_labels_qr.py` (3 cases) and the updated `tests/test_api.py` |
| `git diff a773566~1 896163a -- app/labels.py app/main.py tests/` | read in full — see below |
| Live: `production.bins.labels` → downloaded PDF → `pypdf` extracted the page image → `zxingcpp` decoded it | `'BIN:REVA1'` exactly, on a 288×432pt (4×6in) page — matches the bin's code verbatim |

## Input bounds on `/labels/qr`
```python
class QrLabelItemModel(BaseModel):
    code: str = Field(min_length=1, max_length=200)
    caption: str | None = None
    size: Literal["4x6", "2x1"]

class QrLabelsRequest(BaseModel):
    labels: list[QrLabelItemModel] = Field(min_length=1, max_length=200)
    out_key: str
```
- `labels` array: 1–200 items — matches both callers' contract bounds exactly
  (`production.bins.labels`'s `binIds: z.array(Id).min(1).max(200)`, T-6-1's
  `inventory.blankLabels`'s `variantIds` at the same bound). `render_qr_labels` also explicitly
  raises on an empty list as a second line of defense (`app/labels.py:159-160`).
- `code`: 1–200 chars. Both real callers only ever send `BIN:<code>` (code ≤ 40 chars per
  `bins.create`'s `z.string().min(1).max(40)`) or `B:<variantId>` (a UUID), both far under 200 —
  the 200 ceiling is headroom, not a live risk. `qrcode`'s own version-fitting (`qr.make(fit=True)`)
  handles any length up to that bound without crashing.
- `size`: a closed `Literal["4x6", "2x1"]` — can't be anything else; `render_qr_labels` indexes
  `QR_LABEL_SIZES_IN` with it directly, so an invalid value would 422 at the Pydantic layer before
  ever reaching that code.
- **Gap (not blocking):** `caption` has no `max_length` — unlike `code`, it's an unbounded
  `str | None`. `render_qr_labels` truncates it for display (`item.caption[:40]` / `[:60]`,
  `app/labels.py:179`/`196`) so it can't distort the PDF, but nothing stops a caller from sending a
  very large string before that truncation happens. Low severity: this endpoint isn't
  internet-facing (only `invai-backend` calls it, over the internal `IMAGING_URL`), and both real
  callers already bound their own caption source (`bins.labels` sends `Bin.name`, capped at 80
  chars by `bins.create`'s schema; `inventory.blankLabels`'s caption is a variant description,
  similarly bounded upstream). Worth adding `Field(max_length=200)` or similar for defense in
  depth, but no live path can currently exploit it.
- `out_key` is an unconstrained `str`, same as the pre-existing `/labels/mock` endpoint's
  `out_key` — consistent with that existing convention (backend generates it via `objectKey()`,
  never user input), not a new gap this card introduces.

## Rendering correctness
- The QR encodes `item.code` verbatim (`_qr_reader(item.code)`, `app/labels.py:171`/`185`) — no
  reformatting, so `BIN:A1` and `B:<variantId>` round-trip exactly, confirmed live above and by
  `tests/test_labels_qr.py`'s own decode-back assertion.
- Page size is set per item via `c.setPageSize(...)` before each `showPage()` — a mixed batch of
  `4x6` and `2x1` items in one request renders each at its own requested size, not the first
  item's size for the whole document (checked `render_qr_labels`, `app/labels.py:161-201`; the
  canvas is constructed with the first item's size only as the initial page, then
  `setPageSize` overrides it per page).
- `ERROR_CORRECT_M` + `box_size=6` is a reasonable choice for a shelf/bin label meant to survive
  handling; consistent with the sandbox carrier label's own QR usage.

## Checks
- [x] Only owned paths changed: `app/labels.py` (new `render_qr_labels`/`QrLabelItem`/
  `QR_LABEL_SIZES_IN`), `app/main.py` (new `/labels/qr` route + its two Pydantic models,
  `896163a`'s one-line rename of the request field to `labels`), `tests/test_api.py` (bounds
  smoke test), `tests/test_labels_qr.py` (new, decode-back tests).
- [x] Nothing outside scope: the two-commit split (`a773566` then `896163a` renaming the field)
  is a real, minimal fix to match T-6-1's already-landed caller rather than asking that commit to
  change — a reasonable call, not scope creep.
- [x] Tests exercise the behavior, none weakened: `scan-test-weakening.sh invai-imaging
  a773566~1` → no hits (run as part of the primary review). `test_labels_qr.py`'s decode-back
  assertion is real proof, not a mock of the unit under test.
- [x] No PII, no money, N/A for tenancy (imaging has no tenant tables) — this endpoint only ever
  sees a `code`/`caption` string and an S3 key, both already scrubbed by the caller.
- [x] Idempotency: rendering a PDF twice for the same bin/variant is a pure, side-effect-free
  render to a fresh S3 key each call — no external cost, no duplicate physical action triggered
  automatically (a human still has to open and print the PDF). This differs from the "label buys"
  CLAUDE.md flags as needing idempotency keys (actual carrier purchases), which this isn't.

## Blocking findings
None in this endpoint. (The reviewer and architect co-reviews found a blocking state-machine gap
in `invai-backend`'s `markSheetPrinted`, unrelated to imaging — see `T-6-2-reviewer-r1.md`.)

## Optional notes (not blocking)
- Add `Field(max_length=200)` (or similar) to `caption` on `QrLabelItemModel` for defense in
  depth, matching `code`'s bound — see the gap noted above.
