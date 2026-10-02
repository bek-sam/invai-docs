# imaging-engineer memory

Seeded 2026-09-26 from `team/lessons.md` (T-16-3); every line below is a row there. Add your own entries under "Learned on cards": date, card, what you learned. No PII or secrets.

## Lessons that apply to you
- 2026-09-26 W8: Never `git stash`, `reset` or `checkout --` in a shared tree; compare in your own worktree at the base commit.
- 2026-09-26 W8: Don't push. Only the tech lead pushes, after the gate (a builder once pushed 44 ungated commits).
- 2026-09-25 W3: Shared files: stage only your hunks (`git add -p` / `git apply --cached`), check `git diff --cached`, then commit.
- 2026-09-24 W2: Kill only PIDs you started (`lsof -ti :<your port>`); never `pkill`/`killall`.
- 2026-09-25 W6/7: Never run `pnpm` inside a worktree; call `node_modules/.bin/*` directly. Never re-link shared `node_modules`.
- 2026-09-25 W3: Poll long jobs inside your turn with short sleeps; don't end your turn to wait.

## Learned on cards
- 2026-09-30 T-P1-2: Never call `pyvips` `icc_transform(embedded=True)` unconditionally in a hot path (`to_srgba`). Measured live: ~2ms/design (1.3MP) to ~20ms/design (15MP) even with no embedded profile, vs ~0.03ms for the naive `colourspace()` path — paying it on every design blew the 25% full-sheet-compose regression budget. Gate it on `img.get_typeof("icc-profile-data") != 0` first; the naive `colourspace()` fallback already converts CMYK correctly with no profile (verified: identical numbers to `icc_transform`'s own no-profile fallback), so gating loses no correctness.
- 2026-09-30 T-P1-2: pyvips `icc_transform("srgb", embedded=True, ...)` never raises on a missing or garbage `icc-profile-data` field — it silently falls back to the same generic conversion `colourspace()` would do. The `except pyvips.Error` guard around it is defensive, not load-bearing, in this pyvips/libvips version (3.2/8.18.6).
- 2026-09-30 T-P1-2: For a whole-sheet option like DTF `mirror`, flip only the per-design artwork layer in `compose.py`, never the label/header/cut-guide layers — a mirrored QR is not a standard scannable code, and the label is read by a human presser, not pressed onto the garment. Verified live with `zxingcpp` that both still decode on a mirrored sheet.
- 2026-09-30 T-P1-2: When a card's film-use metric (B-41) is worded as "Compose returns X across the sheet set", check whether `/compose` actually has visibility into sibling sheets first — it doesn't (one call = one physical sheet). `/nest` returns the full sheet set in one response and is where a cross-sheet aggregate naturally belongs; I implemented it there instead and flagged the wording mismatch in my report rather than guessing silently.
- 2026-09-30 T-P1-2 round 2: Any new `flags[].code` (or other enum-like string) added to an imaging response must be checked against `invai-backend/src/integrations/imaging/client.ts`'s zod schema before shipping — it uses closed `z.enum([...])`, not an open string, so a new code makes an existing caller's response-shape parse throw on every call that hits it (proven live, not a type-level catch). The fix pattern: make the new codes opt-in via a request flag (default off, filtered out of the response) rather than touching the contract/backend — that's the coordinated-card path, not mine.
