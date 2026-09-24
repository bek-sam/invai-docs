# InvAI demo guide — 15 minutes

Audience: a pilot DTF shop owner. Goal: show the golden path — an order comes in, and InvAI
takes it all the way to a shipped label and a profit number, without anyone pressing the wrong
shirt. Everything below runs against the seeded demo shop, **Desert Bloom Tees**, with the
platform already running (`pnpm dev:all` from `invai-infra`, then `pnpm db:seed` once from
`invai-backend` if you haven't — see the workspace `README.md`).

Two browser windows help: one for the web dashboard (owner), one for the floor tablet (or a
second browser profile at http://localhost:5174, since a real 10-inch tablet won't be at hand).

## Before you start

- Web: http://localhost:5173, log in as **owner@desertbloom.test / demo1234!**.
- Floor: http://localhost:5174 — pairing and PIN login happen in step 7.
- Say up front: "Everything you're about to see runs on my laptop, no cloud services, and every
  external integration (Claude, EasyPost, Shopify, S&S) is either the real API or a mock that
  behaves like it — the shop can't tell the difference until we add a key."

## 1. Today (2 min) — the command center

Land on **Today** (the first thing after login). Point out:

- **Due today / at risk / blocked** counts — this replaces the spreadsheet a shop owner keeps
  today to know what's late.
- **Work by station** — how many items are sitting at pick, press, QC and pack right now.
- **Needs attention** — orders blocked because a SKU isn't mapped or artwork failed a check.
- The **Import CSV / Build sheets / Buy labels** quick actions at the top — these are shortcuts
  to steps 2, 4 and 9. Everything in this demo is one or two clicks from Today.

*What the audience should notice:* this is one screen instead of five browser tabs (marketplace,
spreadsheet, ShipStation, a notebook for the vendor).

## 2. Import a CSV order (2 min)

1. From Today, click **Import CSV** (or **Settings → Channels**, then **Import** on a channel).
2. Pick the **Etsy** or **Amazon** connection and a CSV export format, upload any small sample
   order file (a real Etsy/Amazon/TikTok/Walmart order export, or reuse one of the seed's own
   files if one is at hand).
3. The import report shows **New orders**, **Updated**, **Unchanged**, **Rows failed**, and — the
   important number — **N items need SKU mapping**, with a **Map them now** link.

*What the audience should notice:* re-importing the same file updates orders instead of
duplicating them, and nothing gets stuck silently — every row that fails or needs a decision is
called out by name.

## 3. Map a SKU (2 min)

1. Click **Map them now** (or **Catalog → SKU Mapping** in the left nav).
2. The page lists unmapped channel SKUs next to a suggested design + blank, scored by confidence.
   Click **Suggest mappings** to have Claude (or the mock provider, if no key is set) propose one
   for a batch, or **Accept N at ≥80%** to bulk-accept the confident ones.
3. Map one manually: pick a row, choose a design and a blank variant/size, save. Point out the
   **Save as rule** option — the same channel SKU never needs mapping again.

*What the audience should notice:* mapping is a one-time cost per SKU, not per order. A rule
saved today silently unblocks every future order with that SKU.

## 4. Personalization proof (1–2 min)

1. Go to **Catalog → Personalization**, tab **Artwork review**.
2. Open a flagged item (filter by status if the list is long). It shows the rendered proof at
   300 DPI, the buyer's original answer, and any flags — **overflow** (text shrank and still
   didn't fit), **too_long**, **suspicious_chars**, or **empty**.
3. Edit the text inline if needed and click **Approve**, or use a suggested fix if one is offered.

*What the audience should notice:* a personalized order (a name, a date) gets checked and proven
before it's ever printed — no more shipping a shirt with a name cut off at the collar.

## 5. Build a gang sheet (2 min)

1. Go to **Production → Gang Sheets**, click **Build sheets**.
2. The build panel groups ready items into a 22-inch sheet, nested automatically (rotation
   allowed, ~0.25" spacing). Rush items go in first. Confirm the build.
3. Open the built sheet: a full preview with every design placed, and under each one a QR code
   plus printed order/item/size/color/design text — this is what gets scanned at the press.

*What the audience should notice:* this is the product's core differentiator — no other tool in
this space nests and labels a gang sheet automatically, per unit, so a presser never has to guess
which shirt goes where.

## 6. Send it to the vendor (1 min)

1. Still on the sheet, or from **Settings → Vendors**, show **Sun City DTF** already connected
   (invited vendors show as `active` once they open their own portal).
2. Send/share the sheet to the vendor. Switch browser windows (or log out) and sign in as
   **vendor@suncitydtf.test / demo1234!** to show the vendor's own view: **Sheet inbox** lists
   incoming sheets, **Shops** lists the shops that invited this vendor. The vendor marks a sheet
   printed/shipped from here — that's the only thing a vendor ever sees of the shop's data.

*What the audience should notice:* the vendor gets exactly one screen, scoped to only what that
shop shared with them — not a login to the shop's whole system.

## 7. Floor tablet: pair, log in, press-scan (3 min)

This is the step that stops a wrong shirt from ever reaching a customer.

1. **Pair the tablet** (skip if a station is already paired for this demo): as the owner, go to
   **Settings → Stations**, click **Pair tablet** next to **Press 1**. A QR code and a
   one-time copyable token appear.
2. On the floor tablet (http://localhost:5174), scan the QR — or if a real camera isn't handy,
   copy the token and paste it into the setup screen's text field.
3. **Log in** with a PIN: presser Pat is `1155` (or the second presser, Luis, `1188`). PINs are
   personal — the tablet stays paired to the station; a different staff member's PIN on the same
   tablet logs in as them.
4. Go to **Press**. Scan the transfer's QR code first (from the gang sheet printout, or use the
   dev scan icon at the bottom right / `?dev=1` to simulate a scan without a real scanner).
5. **Right blank:** scan the correct blank (its own UPC/barcode). The screen flashes full-screen
   green **PRESS** — the shirt is confirmed correct, go ahead and press it.
6. **Wrong blank:** scan a different blank than what's expected. The screen flashes full-screen
   red **BLOCKED**, showing **Expected** vs **Scanned**, with a reason such as `wrong_style` or
   `wrong_design`. Nothing lets the presser proceed past this screen with the wrong shirt.

*What the audience should notice:* this single screen — scan transfer, scan blank, big
green/red result — is what makes "we shipped the wrong design" go away. It also works offline
(the tablet queues scans in IndexedDB and replays them when the network comes back).

## 8. QC (1 min)

1. On the tablet (or a second paired QC station), go to **QC**. Scan or select a pressed item.
2. **Pass** moves the item to packed-and-ready. **Fail** asks for a reason (misprint, wrong
   blank, damaged, etc.) and creates a reprint — the item goes back to the queue, the blank isn't
   silently lost.

*What the audience should notice:* QC failures are tracked with a reason, so at the end of the
month the shop can see *why* shirts get reprinted, not just that they do.

## 9. Pack and buy a label (2 min)

1. On the **Pack** station, scan the order's items; the screen shows progress and warns if
   something's missing. Once every item in the order is packed, the order moves to the shipping
   queue.
2. Back in the web dashboard, go to **Shipping** (or click **Buy labels** from Today). Pick the
   order, get a rate (EasyPost live or mock, whichever key is set), buy the label. A 4x6 PDF is
   generated and tracking is queued to push back to the marketplace.

*What the audience should notice:* nothing can be packed as complete with a missing item — the
pack station enforces it — and the label purchase is the same click whether it's the mock carrier
or a real EasyPost account.

## 10. Profit (1 min)

Go to **Analytics → Profit**. Show profit sliced by order, by design, by blank and by channel —
point at one specific design and show its true margin after channel fees, shipping cost and
blank cost, not just revenue.

*What the audience should notice:* "which designs actually make money" is usually a spreadsheet
nobody keeps up to date. Here it's live.

## 11. AI listing + trademark check (2 min)

1. Go to **Listings → AI Drafts**, click **Draft listings**, pick a channel and a design.
2. Open the generated draft: title, tags, description, live-validated against that channel's
   rules (length, tag count), plus a **Trademark** section showing the risk check against a
   seeded database of registered clothing marks.
3. To show a risk hit on demand, go to **Listings → Trademark**, type a well-known brand name
   (e.g. "Nike") into **Text to check**, click **Check risk** — it comes back flagged. Approving
   a flagged draft requires an explicit **Approve anyway** confirmation.

*What the audience should notice:* the shop never gets an Etsy IP strike from an AI-written
listing that accidentally used a trademarked term, because the check runs before a human signs
off, not after a complaint.

## 12. Assistant (1 min)

Go to **Assistant**. Ask one of the suggested questions, e.g. *"Which blanks will run out in the
next 7 days?"* or *"How many orders are at risk of shipping late?"*. The assistant answers using
only this shop's real data (read-only, company-scoped tools) — no buyer names or addresses are
ever sent to the model.

*What the audience should notice:* this is a text box that answers with the shop's own numbers,
not a generic chatbot.

## Wrap-up line

"Everything you just saw — the order, the sheet, the scan, the label, the profit number — is one
system. Nothing here required exporting a spreadsheet or logging into a different tool."
