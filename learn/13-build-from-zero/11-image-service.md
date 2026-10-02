# Lesson 13.11 — The image service: a tiny gang-sheet layout with FastAPI + pyvips

## 1. In one sentence
You'll build a small Python FastAPI service with one endpoint that packs a list of
rectangular designs onto the fewest/shortest sheets possible (a simplified version of
gang-sheet nesting) and a second endpoint that actually composites real images onto
one sheet with pyvips, returning a real PNG you can open and look at.

## 2. Why it exists
DTF printing works in physical inches, not pixels: a shop buys film by the linear
inch, so "how tightly can we pack these designs onto one sheet" is directly a money
question — a sloppy layout wastes film on every single sheet, every single day.
InvAI keeps this work in a separate Python service (not Node) because the actual
image library doing the heavy lifting, **pyvips**, is a Python binding to libvips —
a streaming image library that can composite large images using a small, fixed
amount of memory, which matters a lot when a "sheet" can be several feet long at
print resolution.

The nesting problem itself (pack rectangles onto a sheet with as little wasted space
as possible) is a real, well-studied bin-packing problem — this lesson builds a
version small enough to read in five minutes, not a production-grade packer.

## 3. How it works

### Step 1 — the service
```bash
cd ~/invai-from-zero
mkdir imaging && cd imaging
uv init --python 3.13
uv add fastapi uvicorn pyvips pillow
```

### Step 2 — a tiny nester
Pack items by height into rows on a fixed-width sheet (a simplified shelf packer —
not optimal, but genuinely functional and easy to reason about):
```python
# app/nesting.py
from dataclasses import dataclass

@dataclass
class Item:
    id: str
    width_in: float
    height_in: float

@dataclass
class Placement:
    item_id: str
    x_in: float
    y_in: float

def nest(items: list[Item], sheet_width_in: float, gap_in: float = 0.25) -> tuple[list[Placement], float]:
    placements: list[Placement] = []
    x = gap_in
    y = gap_in
    row_height = 0.0
    for item in items:
        if x + item.width_in > sheet_width_in:   # doesn't fit this row -- start a new one
            x = gap_in
            y += row_height + gap_in
            row_height = 0.0
        placements.append(Placement(item.id, x, y))
        x += item.width_in + gap_in
        row_height = max(row_height, item.height_in)
    total_length_in = y + row_height + gap_in
    return placements, total_length_in
```
The `gap_in` between items isn't decoration — it's the real-world cutting margin a
pressing/cutting process needs between designs; InvAI's real default is 0.25 inches.

### Step 3 — composite real pixels with pyvips
```python
# app/compose.py
import pyvips

def compose_sheet(placements, images: dict[str, str], width_in: float, length_in: float, dpi: int, out_path: str):
    W, H = round(width_in * dpi), round(length_in * dpi)
    sheet = pyvips.Image.black(W, H, bands=4).copy(interpretation="srgb")  # transparent canvas
    for p in placements:
        layer = pyvips.Image.new_from_file(images[p.item_id], access="sequential")
        x_px, y_px = round(p.x_in * dpi), round(p.y_in * dpi)
        sheet = sheet.insert(layer, x_px, y_px)
    sheet.write_to_file(out_path)
```
`access="sequential"` is a real pyvips performance detail: it tells libvips it can
stream the source image top-to-bottom instead of loading the whole thing into memory
at once — the difference between composing a few images comfortably and running out
of memory on a long sheet.

### Step 4 — the endpoint
```python
# app/main.py
from fastapi import FastAPI
from pydantic import BaseModel, Field
from . import nesting, compose

app = FastAPI(title="fromzero-imaging")

class ItemIn(BaseModel):
    id: str
    width_in: float = Field(gt=0, le=60)
    height_in: float = Field(gt=0, le=240)

class NestRequest(BaseModel):
    items: list[ItemIn]
    sheet_width_in: float = Field(gt=0, le=60)

@app.post("/nest")
def nest_endpoint(req: NestRequest) -> dict:
    placements, length_in = nesting.nest(
        [nesting.Item(i.id, i.width_in, i.height_in) for i in req.items], req.sheet_width_in,
    )
    return {"placements": [p.__dict__ for p in placements], "length_in": length_in}
```
Notice `Field(gt=0, le=60)` on `width_in` — Pydantic validates physical bounds at the
API boundary, the same role Zod plays in lesson 13.2's TypeScript contract.

### Step 5 — exercise it for real
```bash
uv run uvicorn app.main:app --port 8100 &
curl -s -X POST localhost:8100/nest -H 'content-type: application/json' -d '{
  "items": [{"id":"a","width_in":4,"height_in":5}, {"id":"b","width_in":4,"height_in":5}],
  "sheet_width_in": 10
}'
```
Then wire up `/compose` with two real small PNGs and actually open the output file —
measure it (pixels ÷ dpi should equal the inches you asked for) rather than trusting
that "it ran without an error" means it's correct.

## 4. In our code
- `invai-imaging/app/nesting.py:22-41, 133` — the real `Item`, `Placement`, `Sheet`
  dataclasses and the real `nest()` function — a proper packer (not a simple shelf
  packer), but solving exactly the problem your Step 2 solved at a smaller scale.
- `invai-imaging/app/compose.py:28, 47, 341-356` — the real pyvips usage: `import
  pyvips`, `pyvips.cache_set_max(0)` (disables libvips's own cache — deliberate, so
  memory use stays predictable across many compose calls in one process), and the
  real `pyvips.Image.black(...)`/`.insert(...)` pattern your Step 3 copied.
- `invai-imaging/app/main.py:314-337` — the real `/nest` endpoint, including a
  length-weighted `overall_utilization()` across a whole sheet set — the actual
  number this project tracks as its film-efficiency metric (module 05.2 covers a
  real incident where unrealistic seed sizes made this number look artificially bad
  until the seed was fixed).
- `invai-imaging/app/main.py:343-396` (`ComposeRequest`) — real Pydantic field
  bounds (`width_in: float = Field(gt=0, le=60)`) at the exact API boundary your
  `ItemIn` model echoed, plus a `@model_validator` enforcing a PDF-specific length
  cap — physical-size and format limits checked as part of validation, not as an
  afterthought deep in the compose logic.
- Module 03.5 (imaging) and the `imaging-change-with-budget` playbook — the full
  budget this project holds every imaging change to: exact physical size, scannable
  QR labels, peak RSS, a decode pixel cap, and the 0.25in gap/margin, 150 DPI floor
  defaults your Step 2's `gap_in` mirrored.

## 5. What it uses
- **FastAPI** — a Python web framework with request/response validation built on
  Pydantic; module 03.5 covers why this over Flask for a service whose inputs need
  real validation (physical sizes, DPI ranges) at the boundary.
- **pyvips** — Python bindings to libvips, a streaming image-processing library
  that can composite very large images without loading them entirely into memory —
  the reason this service exists in Python rather than reusing a Node image library.
- **Pydantic** — the validation layer FastAPI is built on; its `Field(gt=..., le=...)`
  bounds play the same "validate at the boundary" role Zod plays on the TypeScript
  side (lesson 13.2).

## 6. Try it yourself
1. Pass a `width_in` of `0` or `100` (outside `Field(gt=0, le=60)`'s bounds) to your
   `/nest` endpoint and read FastAPI's actual 422 response body — compare it to
   lesson 13.2's `COMMON_ERRORS` shape. Are both "a validation failure," expressed
   the same general way?
2. Run `uv run ruff check .` and `uv run pytest` on your tiny imaging service (even
   with zero tests written yet) — this is the exact command the real
   `imaging-engineer` role runs as its definition of done.
3. Composite three overlapping placements (make two items' `x_in`/`y_in` overlap on
   purpose) and open the resulting PNG. Does `pyvips.Image.insert` let you place one
   image on top of another silently, or does it error? What would a real nester need
   to check *before* composing to prevent this from ever happening?

## 7. Common mistakes
- Working in pixels first and converting to inches as an afterthought. DTF print
  decisions (film cost, label size, sheet length limits) are fundamentally physical
  measurements; starting from inches and multiplying by DPI only at the last step
  (as this lesson's `compose_sheet` does) keeps the physical meaning attached to
  every number, instead of losing it in a pixel count that only makes sense at one
  specific DPI.
- Loading every source image fully into memory before compositing, instead of using
  `access="sequential"` (or otherwise letting libvips stream). It's invisible on a
  tiny two-item test and a real problem the moment a sheet has dozens of designs or
  runs several feet long.
- Skipping bounds validation on physical inputs ("it's just a demo, who's going to
  send a negative width"). A validated API boundary is what turns a bad input into a
  clear 422 instead of a confusing crash (or worse, a sheet quietly composed wrong)
  three function calls deep.

## 8. Check yourself
<details>
<summary>1. Why does this project use pyvips/libvips instead of a more common
Python imaging library like Pillow for the actual compositing?</summary>

libvips is built to stream large images through a small, fixed memory footprint
rather than loading them fully into RAM, which matters when a gang sheet can be
several feet long at print resolution. A library that loads everything into memory
first scales much worse as sheet size grows.
</details>

<details>
<summary>2. What does <code>Field(gt=0, le=60)</code> on a width field actually
prevent, concretely?</summary>

It rejects a request with an impossible or nonsensical physical width (zero,
negative, or absurdly large) at the API boundary, with a clear validation error —
before that value ever reaches layout or compositing code that assumed it was
already sane.
</details>

<details>
<summary>3. Why does this lesson convert inches to pixels (<code>width_in *
dpi</code>) only inside the compose step, rather than working in pixels from the
very beginning?</summary>

Because the physical size (in inches) is the thing that actually matters for cost
and correctness — DPI is just a rendering detail. Keeping the data model in inches
until the last possible step means the same placement data could be rendered at a
different DPI without recomputing the whole layout, and a human reading the data can
reason about it in real-world terms.
</details>

## 9. Words to know
- **pyvips / libvips** — a streaming image-processing library (and its Python
  binding) that composites large images using a small, bounded amount of memory.
- **DPI (dots per inch)** — the resolution a physical size is rendered at; `pixels
  = inches × DPI`.
- **Nesting** — packing multiple designs onto one sheet with minimal wasted space;
  a bin-packing problem in InvAI's specific physical-inches context.
- **Pydantic** — the Python data-validation library FastAPI is built on.
