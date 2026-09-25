# Review of T-2-2 (round 1)

- Reviewer: product-designer on Opus
- Author: web-engineer on Opus 5.5
- Verdict: approve

## Evidence I re-ran

Same setup as the `reviewer` file (worktrees + DB copy + own API/web, later reclaimed by the tech
lead after my screenshots were already taken — findings below stand). I walked the billing page as
the owner (the only role with `billing.manage`), forced every `BillingStatus`, and triggered the
plan-limit dialog for real by inviting an 8th person on a 5-seat Starter plan. Screenshots I took
and looked at (not saved anywhere permanent, since the worktree was cleaned up — described in
detail below and cross-checked against the author's own screenshots in
`invai-docs/waves/2/reports/T-2-2/`, which I also looked at):
`billing-starter-active`, `banner-trialing-3d`, `billing-trialing-3d`, `banner-past-due`,
`banner-trial-expired`, `billing-trial-expired`, `limit-dialog-en-1440`, `limit-dialog-es-390`,
`billing-active-growth-{en,es}-390`.

| Command | Result |
|---|---|
| `./node_modules/.bin/vitest run --passWithNoTests` (invai-web) | 37/37 passed |
| `./node_modules/.bin/vite build` | built clean |

## Design read

**Prevent the expensive mistake / show urgency honestly.** The banner hierarchy is right: a
7-day trial warning is amber and dismissible for the session; past-due and trial-expired are red
and cannot be dismissed, and both name the real consequence in plain words ("Order imports and
label buying are paused until you choose a plan") rather than a vague "action needed." Status
colors match the rest of the app's `StatusBadge` conventions (green=active, blue=trial, red=past
due/expired, gray=cancelled). The two usage meters that are over their limit show red **and** the
words "limit reached," not color alone — this is the one place the card explicitly asked for that,
and it's done correctly for both `users` and `connections` simultaneously in my Starter test.

**Plain shop words / no raw text.** I forced a real `PLAN_LIMIT_REACHED` (not injected) by inviting
past the Starter seat limit. The result is a two-layer message that reads naturally in the field: a
toast ("Your plan's limit is reached. Go to Billing to upgrade.") plus a dialog that says exactly
what hit the wall and by how much ("Your plan allows 5 people. Upgrade to invite more."), never the
server's own words. In Spanish this holds up completely at 390 px — no truncation, no leftover
English, buttons stack instead of overflowing ("Ir a Facturación" / "Ahora no").

**Accessible by default.** The dialog is a proper modal: labelled by its own translated heading
(`aria-labelledby` → "You've reached your plan's limit" / "Llegaste al límite de tu plan"),
described by its own body text, focus lands inside it on open, Tab cycles only through its three
controls, and Escape closes it. When it opens over the still-open Invite dialog, Radix correctly
`aria-hide`s the one underneath rather than leaving two dialogs readable to a screen reader at once.
Money is legible and consistent (`$149.00/mo`, `$0.05 per label`, `$8.28 label fees`) — no cents
leaking through anywhere I checked.

**Speed for repeat work.** The plan cards read at a glance (current plan pinned with a border +
badge, Upgrade/Downgrade labelled by direction rather than a generic "Switch"), and the downgrade
and move-to-free actions both explain the concrete new limits before asking for confirmation
(author's `downgrade-confirm-…` screenshot, which I looked at) — that's the right amount of friction
for something that can quietly break an owner's workflow later in the month.

**Phone width.** 390 px in both languages: no horizontal scroll (`scrollWidth === clientWidth`),
cards stack to one column, the plan price and meters stay legible, the banner's dismiss/action
buttons remain reachable and don't overlap the message text.

## Findings

None blocking. One non-blocking design note, already flagged in the reviewer's file: the Invite
dialog stays open (with its filled-in name/email) behind the plan-limit dialog rather than closing.
I'd keep this — it avoids losing what the office worker just typed — but wanted to record the
choice was noticed, not missed.

## Checks
- [x] Only owned-by-others paths I can comment on (`invai-web/**`) match the card; nothing in
      `invai-ui` was touched by this card (verified: `git show --stat e37e716` has no `invai-ui`
      changes; this card doesn't add or change shared components)
- [x] Copy is plain language, en and es, matched pair by pair for every new key
      (`billing.*`, `billingBanner.*`, `upgrade.*`, `billingStatus.trial_expired`)
- [x] Accessible: labelled dialog, focus trap, Escape, color never used alone for limit state
- [x] 390 px verified in both languages, no overflow

## Optional notes (not blocking)
- Plan names ("Trial", "Growth", …) come from the server catalog untranslated — already logged by
  the author as a known gap, correctly out of this card's scope.
- `formatDate` uses the browser locale rather than the app's language toggle, and drops the year —
  pre-existing behavior, not introduced here; worth a small follow-up card if a Spanish-reading
  owner's browser is set to `en-US`.
