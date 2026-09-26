# Review of T-13-1 (round 1)

- Reviewer: architect (co-review) on Sonnet 5
- Author: architect + floor-engineer + backend-foundation on Opus 5.5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| Read `invai-docs/waves/13/wave.md` §"T-13-1: version-handshake design (r1)" and `invai-docs/decisions/0012-floor-contract-compat.md` | design intent: minimum lives in backend config specifically so ops can hold it back "without a contracts release"; ADR §5/§6 promise a 14-day pinned grace window and note the "every bump forces update unless ops pins it lower" consequence |
| `git -C invai-backend show 586b7de -- src/env.ts src/api/orpc.ts src/lib/errors.ts` | `MIN_FLOOR_CONTRACT_VERSION: z.string()....default(CONTRACT_VERSION)`; `enforceFloorContractVersion` gated on `mode !== "floor" && mode !== "station"` and `sessionKind === "user"` exemption, runs after the auth switch in `guard` |
| `git -C invai-contracts show 35048ff -- src/compat.ts src/contract/_base.ts` | `CONTRACT_VERSION` is a literal pinned by a same-package test to `package.json`; `CLIENT_TOO_OLD` added with `{minVersion, current}`, 426 |
| `pnpm --dir invai-backend vitest run src/api/contract-version.test.ts` (`perl -e 'alarm 120; exec @ARGV'`) | 11/11 passed, including the "web-only procedures" and "web user session" exemption case |
| `git -C invai-backend diff --stat origin/main -- src/api/orpc.ts src/env.ts src/lib/errors.ts src/api/app.ts` | matches T-13-1's owned/granted paths exactly, no drift into T-13-3's or T-13-2's territory |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Version header, backend minimum | Yes | header sent on every floor RPC; minimum is backend env config as designed |
| 2. Typed error + translated screen | Yes | `CLIENT_TOO_OLD`/426 end-to-end, `UpdateNeededScreen` en/es |
| 3. Old queued writes never silently lost | Yes | `stale_version` park path confirmed non-destructive |
| 4. Compatibility policy documented | Partially — see finding | ADR 0012 exists and is well-written, but its own §5 promise (14-day pin holds) isn't backed by the mechanism in §2/§6 (default = current build's version) |
| 5. Tests | Yes | re-ran, green |

## Blocking findings
1. **Design-level, `invai-backend/src/env.ts` default + `invai-docs/decisions/0012-floor-contract-compat.md` §2, §5, §6** — this is the wave.md r1 design I signed off on, and on a second look it has a real gap: tying `MIN_FLOOR_CONTRACT_VERSION`'s *default* to the backend's own build-time `CONTRACT_VERSION` conflates "current" with "oldest still-compatible." Those are only the same thing if ops re-asserts an override on literally every deploy that isn't itself a floor-facing breaking change — additive contracts bumps (next up: T-13-3, then T-13-2's own CI changes, then every future wave that touches `invai-contracts` for any reason, web-only or not) all silently raise the effective floor minimum the moment they deploy, unless someone remembers to hold it down. Worse, during an actual breaking-change grace window the same fragility applies in reverse: the pin has to survive every intervening deploy for 14 straight days, including unrelated hotfixes, or the window closes early with no signal that it did.
   - This isn't a minor ops inconvenience — it directly undermines the one guarantee wave 13 exists to deliver ("old floor tablets can't corrupt data after a deploy" and, per ADR 0012, "aren't unnecessarily forced to update either"). A default that requires perfect, indefinite ops discipline to avoid either outcome is not a control; it's a control that degrades to whichever failure mode ops forgets about first.
   - **Fix**, entirely inside T-13-1's owned files, so it belongs on this card rather than a follow-up: add a second constant to `invai-contracts/src/compat.ts` — e.g. `FLOOR_COMPAT_BASELINE` — that is hand-bumped only in the same commit that ships a floor/station-facing breaking change (tied to the existing "every bump gets a CHANGELOG line that says whether it affects the floor" rule in ADR 0012 §5, last bullet). Point `env.ts`'s default at that constant instead of at `CONTRACT_VERSION`. The env-var override remains for genuine ops emergencies (rollback, holding a bad release back), but it's no longer load-bearing for the routine case. I'll update wave.md's design note and ADR 0012 to match once this lands.

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope (T-13-3/T-13-2 sequencing respected — no `package.json`/`CHANGELOG.md` race)
- [x] Tests exercise the behavior; none weakened
- [x] Tenancy n/a; idempotency preserved (outbox replay semantics unchanged by this card beyond the new park reason); en/es present
- [ ] Decisions recorded correctly — ADR 0012 needs the correction in the blocking finding

## Optional notes (not blocking)
- The `station` mode having no prior auth branch (so first contact gets 426 before any token check) is the right call — it matches the card's "first contact" requirement and doesn't weaken `floor.login`'s own auth.
- Good instinct to keep `CONTRACT_VERSION` a literal pinned by test rather than a JSON import (avoids the Node/tsx/Vite import-attribute mismatch class of bug) — worth calling out in `architecture-as-built.md` for T-13-2 to build its semver check on the same test.
