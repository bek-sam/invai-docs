# Review of T-5-4 (round 1) — product-designer co-review

- Reviewer: product-designer on Sonnet 5
- Author: web-engineer + backend-foundation on Opus 5.5
- Verdict: approve

Scope: the Team and Stations screens, confirmation copy, PIN-only presentation, 390px layout and
en/es parity. Backend correctness/tenancy and the invite-uniqueness/revoke-race questions are the
primary reviewer's and security-reviewer's files (I defer to their `changes-required` on the
revoke race; nothing here blocks on it, since it's an audit-trail bug, not a UI issue).

## Evidence I re-ran
| Command | Result |
|---|---|
| Read `invai-web/src/routes/_app/settings/{team,stations}.tsx` (full diff), `components/confirm-dialog.tsx` (unchanged, reused) | see notes below |
| Screenshots viewed (3, per token budget): `3-team-en.png`, `4-floor-pin-only-signed-in.png`, `7-floor-removed-en.png` | see per-screen notes |
| `git diff 7bf4b3d~1 7bf4b3d -- src/i18n/en.ts src/i18n/es.ts` | 39/39 key additions, 0 deletions, matched 1:1 by name (diffed key lists) |
| `git diff effa695~1 effa695 -- src/i18n/en.ts src/i18n/es.ts` (invai-floor) | 1 key added on each side (`setup.removed`) |
| `git diff eaad60d~1 eaad60d` (invai-ui) | `station.receiving` present in both locale files, same key |

## Per-screen notes

**`3-team-en.png` (Team list with PIN-only rows, after a revoke toast)**
- PIN-only rows ("Lupe Floor 476/477", plain "Lupe Floor") show "PIN only, no email" where the
  email column normally sits, plus a "PIN only" badge next to Status — matches the card's
  requirement to never render the placeholder. Good, and matches `team.tsx`'s
  `row.original.pinOnly ? … : row.original.email` branch.
- Role select is a native dropdown scoped to floor roles for these rows (`options = u.pinOnly ?
  roles.filter(isFloorRole) : roles`) — correct, prevents an accidental promote-off-floor from the
  UI even before the backend's own guard fires.
- The "Invite revoked" success toast is legible against the table without obscuring the row it
  refers to.
- Minor, not blocking: three PIN-only rows are named "Lupe Floor 476", "Lupe Floor 477" and "Lupe
  Floor" with no distinguishing detail beyond the auto-suffixed station-pairing number — that's
  seed/demo data from the report's own test run, not a product default, so I'm not filing it as a
  finding, just flagging it's confusing to look at in a screenshot review.

**`4-floor-pin-only-signed-in.png` (Pack screen, "Lupe Floor 476" signed in)**
- The floor Pack screen shows no trace of the placeholder email or any account chrome beyond the
  person's name and role context ("Pack · Lupe Floor 476") — correct, this is exactly what "can't
  tell it's a synthetic address" should look like from the floor operator's side.
- EN/ES toggle, Online/Live/Synced status and Switch button are all present and unaffected by this
  card — confirms no regression to the existing floor chrome.

**`7-floor-removed-en.png` (Setup screen after a station token revoke)**
- The warning banner ("This tablet was removed in InvAI. Pair it again with a new station QR
  code.") uses `role="alert"` (confirmed in the diff, `SetupScreen.tsx`) and sits above the fold,
  in a high-contrast amber card — good, a presser walking up to a reset tablet gets an explanation
  instead of a bare QR scanner or a stale "Reconnecting" spinner (the pre-fix bug the report
  describes).
- Copy is plain language, names the actor ("InvAI") and gives the next step ("Pair it again with a
  new station QR code") rather than a raw error code — matches the ux-copy bar for error/empty
  states.
- "Try a demo station" link remains visible below the paired form even with the warning shown —
  no layout collision.

## Confirmations (AC3) — copy review
- Owner promotion gets its own stronger copy path (`team.confirmOwnerTitle`/`Body`: "Make {{name}}
  an owner?" / "Owners can do everything, including billing, deleting data and managing other
  owners.") distinct from a same-tier role change ("Change {{name}}'s role? From A to B. It applies
  right away.") — correctly escalates the warning for the one destructive-by-consequence case
  (`destructive={pending.kind !== "role" || pending.role === "owner"}` in `team.tsx`).
- Deactivate body correctly sets expectations across both surfaces it touches ("signed out, can't
  sign in on the web, and their floor PIN stops working. You can reactivate them later.") —
  station-side deactivate copy is the station-specific equivalent ("Staff can't sign in on this
  tablet until you reactivate it.").
- Revoke-token copy for a lost tablet ("Use this for a lost or stolen tablet…") correctly frames it
  as a security action distinct from ordinary deactivation, and states the irreversible-until-repair
  consequence ("can't be used until you pair it with a new token") — good, matches what the reviewer
  verified live (token invalid immediately after revoke).
- Revoke-**invite** copy ("The link in their email stops working. You can invite them again
  later.") is accurate per the current code, though per the primary/security reviewer's finding 1
  it's possible (in the race window) for a revoke to land on an already-accepted invite; the copy
  doesn't over-promise anything wrong here (it only describes what revoke does to the link), so no
  copy change is needed even once that bug is fixed.

## Accessibility
- `team.roleFor` aria-label ("Role for {{name}}") replaces the generic "Role" label on a per-row
  select — correct, a screen-reader user tabbing through many rows now hears which row's role
  control they're on.
- The PIN column's checkmark/dash fix (`<span className="relative"><span aria-hidden>✓/—</span>
  <span className="sr-only">…</span></span>`) is a real fix, not a cosmetic one: the report's
  explanation (an absolutely-positioned `sr-only` span stretched the page past 390px) is consistent
  with a common Tailwind `sr-only` pitfall (`position: absolute` needs a `relative` ancestor with
  bounded width, or it can push layout width in some browsers/table contexts); the screenshots
  confirm 390px with no horizontal scroll.
- PIN-only invite dialog: the "No email: floor PIN only" toggle is a labeled `Switch` inside a
  `<label>` wrapping both the control and its text — keyboard/screen-reader accessible via native
  label association.

## i18n
- Web: 39 new keys, 39 in `es.ts`, verified 1:1 by name (no orphaned/missing key).
- Floor: 1 new key (`setup.removed`) present in both `en.ts` and `es.ts`.
- `invai-ui`: `station.receiving` present in both locale JSONs (AC 6, the wave-4-gate carryover).
- No raw English spotted in any of the 3 screenshots or in the diffed strings.

## Blocking findings
none

## Checks
- [x] Only owned paths changed for the UI surfaces (`routes/_app/settings/{team,stations}.tsx`,
  web's own i18n keys, `invai-ui`'s shared locale files for the one AC 6 key)
- [x] Nothing outside scope
- [x] En/es parity verified by diff, not just spot-checked
- [x] 390px layout and keyboard/aria coverage verified for the changed surfaces
- [x] Confirmation copy correctly scales severity (owner promotion > role change; token revoke >
  deactivate) and states real consequences, not vague warnings

## Optional notes (not blocking)
- Seed data naming ("Lupe Floor 476/477/(no suffix)") makes the team list a little hard to scan in
  a screenshot with 3 PIN-only rows for the "same" person — worth asking QA/seed owners to give
  PIN-only fixtures more distinct names if this becomes a recurring golden-path screenshot.
- Not evaluated: the invite dialog's live states beyond the 2 screenshots provided (e.g., the
  "PIN taken, retry" toast path described in the report) — I'm taking the report's description on
  trust for that one sub-flow since it isn't in the 3 screenshots I reviewed and re-deriving it
  from code reading alone matches the described behavior (`team.pinTaken` toast + `added` state
  short-circuiting to `setPinMut` only on retry).
