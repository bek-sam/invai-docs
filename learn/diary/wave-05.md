# Wave 5 — office web, orders and settings

**Dates:** 2026-09-25 to 26. **Pushed:** wave 5 itself was push-ready; see below for what
complicated the push.

## What was built
- **T-5-1** Order detail actions and shipment section (web-engineer + backend-engineer/
  orders for the address edit): the office can set rush, flags and tags on an order, see
  its shipment, and fix a held address.
- **T-5-2** Channels and shipping settings (web-engineer): connect channels and configure
  shipping from the web app.
- **T-5-3** Onboarding, Today and demo mode (backend-foundation + web-engineer): a
  step-by-step setup flow, the Today screen, and a safe demo mode.
- **T-5-4** Team and stations (web-engineer + backend-foundation for PIN-only staff): manage
  staff and floor tablets from the web app.

## Why
Wave 4 finished the floor side; wave 5 finishes the office side of the same day-to-day
loop — "the office can run a day from the web app... no dead ends." Onboarding and demo
mode matter specifically because InvAI is sold to real shop owners who need to try it
before trusting it with real orders.

## What went wrong
- The gate (`waves/5/gate.md`) found one stale, non-product test assertion that had to be
  fixed before the browser suite was clean — contracts 31/31, ui 20/20, imaging green,
  backend 481/481, web 75/75, floor 86/86, migration 19, API golden path 13/13, browser
  15/15 once fixed, floor 3/3.
- The bigger finding wasn't a bug at all: **wave 6 commits had already landed on top of
  wave 5 on local `main`** in `invai-contracts`, `invai-backend` and `invai-web` — from a
  different card's work landing directly in the gate's shared tree instead of an isolated
  worktree. The gate explicitly declined to decide whether pushing now would push both
  waves together, and flagged it for the tech lead instead of guessing — the same
  judgment call wave 1's gate made about the wave 2 stub commits, and wave 7's gate would
  make again about wave 8.

## What the team learned
- A pattern across waves 1, 5 and 7: when waves overlap in time (because a card's builder
  starts the next wave's work before the current wave is gated and pushed), the *gate*
  is not the place to decide whether to push the overlap through — it reports exactly
  which commits it tested and which ones it found sitting on top, unverified, and leaves
  the push decision to the tech lead.
- Running the next wave's cards concurrently with the current wave's gate is efficient for
  token budget, but it means "wave N's gate" and "what actually gets pushed" are not
  always the same set of commits — reports need to be explicit about which SHAs were
  tested, not just which wave number.

## Files to look at
- `invai-web/src/routes/_app/orders/$orderId.tsx` — order detail actions (T-5-1).
- `invai-web/src/routes/_app/settings/channels*`, `shipping*` (T-5-2).
- `invai-web/src/routes/_app/onboarding/`, `_app/index.tsx` (Today) — T-5-3.
- `invai-web/src/routes/_app/settings/team*`, `stations*` — T-5-4.
- `invai-docs/waves/5/gate.md` — the concurrent-wave-6 finding and the stale-assertion fix.
