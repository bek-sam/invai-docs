---
name: build-floor-flow
description: Build or change a production-floor flow in invai-floor (pick, press, QC, pack, bins, PIN login, station setup) so a mismatch always blocks, scans stay idempotent through the offline Dexie outbox, targets are 64 px+, every result has sound, keyboard-only scanning works, and en/es and demo mode match the server. Use for "floor", "station", "scan flow", "tablet", "press screen", "offline".
---

# Build a floor flow

A tablet flow where a wrong shirt can't be pressed, no scan is lost or doubled, and a gloved Spanish-speaking presser understands every screen at arm's length.

## When to use
- Any change in `invai-floor/**` (floor-engineer): a new station step, a scan code, a result or mismatch reason, offline behavior, login or setup.
- A new server behavior for scans lives in `invai-backend/src/modules/production/floor.ts` (backend-engineer) and the contract (`production.*`, `floor.*`, architect). Coordinate through the tech lead.

## Steps
1. **Read** decision `0002-pack-semantics.md`, `invai-floor/README.md`, `src/scan/pressFlow.ts` (reducer), `src/scan/result.ts`, `src/scanner/wedge.ts` and `useWedgeScanner.ts`, `src/outbox/{db,outbox,sync}.ts`, `src/realtime/sse.ts`, `src/api/{types,rpc,demo}.ts`, the station screen you change in `src/stations/`, and the `production.*` / `floor.*` contract.
2. **Model the flow as a reducer** first (like `pressReducer`) with pure tests (`src/scan/pressFlow.test.ts`): each scan event moves to one state; BLOCKED is a state you only leave with a new, correct scan or the Problem path (`src/components/ProblemDialog.tsx`), which records why.
3. **Scan codes** go through `parseCode()` (`src/lib/codes.ts`): `T:<transferId>`, `B:<blankVariantId>` or UPC/supplier SKU, `BIN:<code>`. A new prefix is added there with tests. The wedge scanner swallows the scan's Enter so a focused button can't fire.
4. **Writes go through the outbox.** Every mutation is an `OutboxCommand` (`src/outbox/db.ts`) enqueued with `enqueue()` before sending; `flushOutbox()` replays strictly in order. Scans carry a `clientScanId` created **once** (`commandId()` uses it as the entry id); never make a new id on retry. The server returns the stored result for a repeated `clientScanId`.
5. **Failure handling** (`src/api/errors.ts` `FailureKind`): `offline` and `unavailable` (network, 5xx, 429, 503, NOT_IMPLEMENTED) pause the queue and retry after 3–60 s showing "retrying", never an error; `rejected` marks that entry failed and the queue continues; `auth` retries once with the current session, then waits for a login. Overload never loses a scan.
6. **Offline checks** run against the cached queue (`useStationQueue`, `QueueCacheRow`) and are labelled "checked on this tablet" (provisional). A later server BLOCKED for a provisional PRESS raises an alert; design for it.
7. **Result screens:** full-screen `ScanResult` (green PRESS / red BLOCKED) from `@invai/ui` with color **plus** icon **plus** words, needs vs scanned for mismatches (wrong size, color, style, design, already pressed, on hold, cancelled), and `feedback("ok" | "error" | "warn" | "tick")` from `src/lib/feedback.ts` on every result (sound plus vibration).
8. **Big and clear:** `BigButton` or `Button size="floor"` (h-20), 64 px+ targets, readable at arm's length on a 10-inch landscape tablet (1280 × 800).
9. **Both backends.** Update the `FloorApi` interface (`src/api/types.ts`), the oRPC implementation (`src/api/rpc.ts`) and the demo backend (`src/api/demo.ts`, `?demo=1`) with the same rules. Demo PINs are 1111, 1122 … 1177.
10. **Strings** in `src/i18n/en.ts` and `es.ts` (typed `FloorStrings`, so a missing key fails typecheck), including errors and problem reasons. Write real Spanish (`write-plain-language-copy`). Hard-coded English in an `@invai/ui` component is a finding for the product-designer, not your edit.
11. **Keyboard only:** the full flow must work from the scanner (a keyboard) with no touch.
12. **Check:** `pnpm typecheck && pnpm lint && pnpm test && pnpm build`, and report the JS bundle size if dependencies changed (budget: initial JS ≤ 150 KB gzip, research 11 §6.1).
13. **Exercise it:** `pnpm dev` with `?dev=1` (simulate-scan box), in demo mode and against the real stack (station token from `invai-backend/seed-output.json`, presser PIN `1155`). Drop the network (browser devtools offline) mid-flow, scan, restore, and confirm the replay produced one result per scan. Screenshot at 1280 × 800 in en and es and look at them.
14. **E2E:** `pnpm e2e` (`e2e/press.spec.ts`: pair, PIN, wrong style/size BLOCKED, right blank PRESS, QC, pack) green on a fresh seed.

## Rules (MUST / MUST NOT)
- MUST block on every mismatch. MUST NOT add any way past BLOCKED without a new correct scan or a recorded Problem. A request to allow it goes to the owner (`escalate-to-owner`), even "for one shop".
- MUST keep scans returning a `ScanResult` for business outcomes; only transport failures are errors.
- MUST NOT generate a new `clientScanId` on retry or reorder the outbox.
- MUST keep en and es complete, sound on every result, and 64 px+ targets.
- MUST get product-designer co-review for UI and qa-engineer for any scan-flow change.

## Done when
- Reducer tests cover the new states, including BLOCKED exits; outbox tests cover replay idempotency.
- `pnpm build` passes; `pnpm e2e` is green on a fresh seed.
- Demo mode and the real stack both run the flow; the offline drop-and-replay was done and one result per scan was seen.
- Screenshots at 1280 × 800 in en and es were looked at.

## References
- `invai-floor/README.md`, `.claude/agents/floor-engineer.md`
- `invai-docs/decisions/0002-pack-semantics.md`, `invai-docs/research/01-shop-workflow.md`
- `invai-backend/src/modules/production/floor.ts` (server scan, `storedResult`)
- `invai-docs/research/12-security-quality-playbook.md` §1.2 (floor PIN and station tokens), §3.7 (targets)
- Related: `idempotent-side-effect`, `add-contract-procedure` (consumer checklist), `add-ui-component`
