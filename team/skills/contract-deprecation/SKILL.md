---
name: contract-deprecation
description: Remove or rename a procedure, field, enum value or event in @invai/contracts without breaking web, floor or the vendor portal - deprecate, keep for a stated period, migrate consumers, then remove. Use for "remove endpoint", "rename field", "breaking change", "drop enum value", or when a provider change forces a contract change.
---

# Contract deprecation

A breaking contract change reaches `main` only after every consumer has stopped using the old shape, and a
cached tablet or browser one version behind keeps working.

## When to use
- Removing or renaming a procedure, input or output field, enum value, outbox event or realtime event.
- Narrowing a type (optional to required, wider enum to narrower, string to UUID).
- A provider change (see `provider-deprecation-watch`) forces the contract to change.
- Adding things is not a deprecation: use `add-contract-procedure`.

## Steps
1. **Write the ADR first** (`record-decision`, `invai-docs/decisions/NNNN-<slug>.md`): what changes, why, the
   replacement, the removal date, and who fixes each consumer. The tech lead plans the consumer cards; a
   breaking change can't slip into one card.
2. **Find every use** of the old shape across the repos that consume the contract:
   ```
   cd ~/Desktop/projects/invai
   grep -rn "<procedureOrField>" invai-backend/src invai-web/src invai-web/e2e invai-floor/src invai-floor/e2e invai-ui/src
   ```
   List each file and its owner in the ADR.
3. **Expand (release 1).** Add the replacement next to the old shape. Mark the old one deprecated so editors
   and the OpenAPI output show it:
   - Procedure: `.route({ method, path, deprecated: true, description: "Use orders.holdItems. Removal after <date>, ADR NNNN." })` (oRPC's `Route` supports `deprecated`).
   - Field: `.meta({ deprecated: true, description: "..." })` (Zod v4 `GlobalMeta.deprecated`), and a `/** @deprecated ... */` JSDoc so TypeScript strikes it through.
   - Enum value: keep it in the enum; stop producing it in the backend; document which value replaces it.
   - Event: emit both old and new names from the backend for the deprecation period.
4. **Backend serves both.** The old procedure delegates to the new service function; a renamed output field is
   filled on both keys. Log each call to a deprecated procedure once per company per day with
   `logger("contracts.deprecated")` so you can see when traffic stops.
5. **Migrate consumers (same wave).** Web, floor and the vendor portal move to the new shape, each through its
   own owner. Floor also updates `src/api/demo.ts`. Web and floor e2e suites must pass on the new shape.
6. **Wait out the old clients.** Keep the old shape for at least one full deploy cycle, and until the
   deprecation log shows no calls for 7 days. The floor PWA caches its service worker; tablets can stay one
   version behind for hours or days (research 11 §4.2).
7. **Contract (release 2).** Remove the old shape in a later wave. Bump the contracts minor version
   (`package.json`, 0.x rule in the README). Run the consumer typecheck loop from `add-contract-procedure`
   step 8; everything must be green before the push.
8. **Partner-facing APIs** (vendor portal `vendorPortal.*`, any future public API): a removal is announced to
   the vendor before the removal release. That message goes out through `send-owner-draft`, never directly.
9. **Close out:** set the ADR status, and note the removal in the release notes (`release-notes`).

## Rules (MUST / MUST NOT)
- MUST NOT remove or rename in the same release that adds the replacement.
- MUST NOT change the meaning of an existing field or enum value in place. A new meaning gets a new name.
- MUST NOT reuse a removed procedure path or event name for something else.
- MUST keep the backend accepting old input until the removal release; it may stop producing old output only
  after consumers stopped reading it.
- MUST keep units stable (cents, inches, `*Pct`, 0..1). A unit change is a rename, never an in-place edit.
- MUST escalate (`escalate-to-owner`) a breaking change to an API a vendor or partner already uses.

## Done when
- The ADR names the replacement, the removal date and each consumer owner.
- Release 1: the deprecated marker is visible, the backend serves both shapes, and consumers are migrated with
  green e2e.
- Release 2: the deprecation log showed no calls for 7 days, the old shape is removed, and every consumer
  typechecks and builds.

## References
- `invai-contracts/README.md` ("A breaking change here is a breaking change everywhere")
- `.claude/agents/architect.md` (additive by default)
- `invai-docs/research/11-platform-scale-playbook.md` §4.2 (one version back and forward)
- `invai-docs/research/12-security-quality-playbook.md` §3.3 (same-day consumer fixes)
- Related: `add-contract-procedure`, `record-decision`, `provider-deprecation-watch`, `release-notes`
