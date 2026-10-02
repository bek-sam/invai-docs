# Lesson 13.9 — The floor app basics: scanning, and an offline queue

## 1. In one sentence
You'll build a tiny tablet-style screen that listens for barcode scanner keystrokes
(a scanner types fast, invisible digits followed by Enter), and queue scan commands
in a browser-local database (Dexie, over IndexedDB) so a scan still gets recorded —
and later, reliably sent exactly once — even if the tablet loses WiFi mid-shift.

## 2. Why it exists
A production floor tablet lives in the real, physical world: a scanner gun, gloves,
a noisy room, and WiFi that drops when the shop's microwave runs. If "no internet"
meant "can't scan," a presser would be stuck mid-shift waiting for a tech problem
that has nothing to do with their job. InvAI's floor app queues every scan locally
first and syncs when it can, so the person scanning never has to think about network
state at all — they scan, they get a response (even if it has to wait a few
seconds), and the data is never lost.

The scanner-detection half exists because a USB/Bluetooth barcode scanner isn't a
separate input device as far as the browser is concerned — it's a keyboard that
types very fast. The app has to tell "someone typing a barcode" apart from "someone
typing in a text field" using nothing but keystroke timing.

## 3. How it works

### Step 1 — detect a scanner burst
A real barcode scanner types each character with almost no gap between keystrokes,
then sends Enter. A human typing the same digits has much larger, uneven gaps.
```ts
// src/scanner.ts
export function createWedgeDetector(maxGapMs = 40) {
  let buffer = "";
  let lastKeyAt = 0;
  return {
    onKeyDown(e: KeyboardEvent, now: number): { code: string } | null {
      if (now - lastKeyAt > maxGapMs) buffer = ""; // gap too big: start over
      lastKeyAt = now;
      if (e.key === "Enter" && buffer.length > 0) {
        const code = buffer;
        buffer = "";
        return { code };
      }
      if (e.key.length === 1) buffer += e.key;
      return null;
    },
  };
}
```
Attach it to the whole window, not a specific input, so a scan works no matter what
the presser has focused — but skip it while a real text field (search box, PIN
entry) has focus, so normal typing there isn't swallowed as a "scan."

### Step 2 — a local, offline-first database
```bash
pnpm add dexie
```
```ts
// src/offline/db.ts
import Dexie, { type Table } from "dexie";

export type OutboxEntry = {
  seq?: number;
  id: string;            // stable idempotency key -- same scan, resent, keeps this id
  kind: "scan";
  input: { code: string; stationId: string };
  status: "pending" | "sent" | "parked";
  attempts: number;
};

export class FloorDB extends Dexie {
  outbox!: Table<OutboxEntry, number>;
  constructor() {
    super("fromzero-floor");
    this.version(1).stores({ outbox: "++seq, &id, status" });
  }
}
export const floorDb = new FloorDB();
```
`&id` makes `id` a unique index — the same scan can be added twice (a retry, a
re-render) without creating two rows.

### Step 3 — enqueue, then try to flush
```ts
// src/offline/outbox.ts
import { floorDb } from "./db";

export async function enqueueScan(code: string, stationId: string) {
  const id = `${stationId}-${code}-${Date.now()}`;
  await floorDb.outbox.add({ id, kind: "scan", input: { code, stationId }, status: "pending", attempts: 0 });
  await flush();
}

export async function flush() {
  const pending = await floorDb.outbox.where("status").equals("pending").toArray();
  for (const entry of pending) {
    try {
      const res = await fetch("http://localhost:3100/rpc/floor/scan", {
        method: "POST",
        body: JSON.stringify({ ...entry.input, clientScanId: entry.id }), // idempotency key
      });
      if (!res.ok) throw new Error(String(res.status));
      await floorDb.outbox.update(entry.seq!, { status: "sent" });
    } catch {
      await floorDb.outbox.update(entry.seq!, { attempts: entry.attempts + 1 });
      // leave as "pending" -- flush() will retry it next time it's called
    }
  }
}
```
`clientScanId` is the same idempotency key pattern from lesson 13.6: if `flush()`
sends the same entry twice (say, the response was lost but the server actually
processed it), the server-side idempotency check — not this client code — is what
guarantees the scan is recorded exactly once.

### Step 4 — exercise it for real
```bash
pnpm dev     # :5174 by convention
```
Open DevTools → Network → set to "Offline," type a barcode-shaped string fast
(simulating a scanner) followed by Enter, confirm it lands in IndexedDB (Application
tab → IndexedDB → `fromzero-floor` → `outbox`, status `pending`). Go back online and
call `flush()` (or wire it to a `window.addEventListener("online", flush)`) —
confirm the row flips to `sent`.

## 4. In our code
- `invai-floor/src/scanner/useWedgeScanner.ts:17-35` — the real
  `useWedgeListener`: `window.addEventListener("keydown", onKeyDown, true)` at the
  app root, `isEditable(target)` to skip real text fields, and the comment
  explaining it "swallows its Enter so it can't click a focused button" — a detail
  your Step 1 skeleton doesn't handle yet.
- `invai-floor/src/outbox/db.ts:92-106` — the real `FloorDB extends Dexie`:
  `outbox!: Table<OutboxEntry, number>` with `"++seq, &id, status"` — the exact
  auto-increment `seq`, unique `id`, and indexed `status` your Step 2 copied.
- `invai-floor/src/outbox/outbox.ts:43-47` — the real `commandId(command)`: for a
  scan, it's `command.input.clientScanId`; for a pack, `input.idempotencyKey` — the
  real idempotency key your Step 3's `clientScanId` was modeled on.
- `invai-floor/src/outbox/outbox.ts:39, 27-37` — `MAX_ATTEMPTS = 5` and the real
  `FlushReport` type (`sent`, `parked`, `stoppedBy`, `resolved`) — a far richer
  retry/give-up model than this lesson's bare `attempts` counter; a "parked" entry is
  one the flush gave up on (rejected, blocked, or the sign-in ended), surfaced to the
  presser rather than silently retried forever.
- Module 05.2 (`05-core-flows/02-gang-sheet-and-floor.md`) — the full flow,
  including why a mismatch (wrong size scanned) always blocks instead of warning.

## 5. What it uses
- **Dexie** — a friendlier API over the browser's built-in IndexedDB, used as the
  floor app's local, offline-capable database; module 03.4 covers why a real local
  database here instead of just `localStorage`.
- **Keystroke-timing scanner detection** — no special browser API for "a barcode
  scanner connected"; a wedge scanner is plain keyboard input, told apart from human
  typing purely by how fast the keys arrive.

## 6. Try it yourself
1. Simulate "the response never arrives" by making your mock `/rpc/floor/scan`
   endpoint hang forever on the first call, then crash the tab mid-request and
   reopen it. Confirm the entry is still `pending` in IndexedDB after reload — it
   survived the crash because it was written to Dexie *before* the network call, not
   after.
2. Scan the same code twice in a row with no server-side idempotency check in
   place, and look at how many rows your backend created. Add the check (lesson
   13.6's `onConflictDoNothing()` pattern, keyed on `clientScanId`) and confirm it
   drops to one even though the client enqueued (and sent) it twice.
3. `grep -n "isEditable" invai-floor/src/scanner/useWedgeScanner.ts` and explain, in
   your own words, why a scanner listener mounted on the whole `window` needs this
   check at all.

## 7. Common mistakes
- Trusting the client's retry count as the only safety net against duplicate
  effects. The client can't know for certain whether a request it never got a
  response for actually succeeded on the server — it has to be able to safely retry,
  which means the *server's* idempotency check (not the client's bookkeeping) is
  what actually prevents a double-effect.
- Detecting a scan purely by "many keystrokes very fast," with no Enter requirement.
  Fast human typing exists too (a quick typo correction, a fast typist); requiring
  the scanner's trailing Enter (or a configured terminator) is what reliably tells
  the two apart in practice.
- Treating a network error during flush as "this scan failed" and discarding it.
  The real app's model is explicit: a retryable failure stays `pending` (or goes
  through backoff) and is retried automatically; only specific, genuinely terminal
  outcomes (rejected, blocked, sign-in ended) get `parked` and shown to the person —
  losing a scan because of a momentary WiFi drop is exactly the failure mode this
  whole lesson exists to prevent.

## 8. Check yourself
<details>
<summary>1. Why can't the client alone guarantee a scan is recorded exactly once,
even with a stable <code>clientScanId</code> and careful retry logic?</summary>

The client can only control *how many times it tries to send* the request — it has
no way to know for certain whether a request that got no response actually reached
and was processed by the server. The actual "exactly once" guarantee has to live on
the server, as a database-level idempotency check keyed on that same id (lesson
13.6) — the client's job is just to make retrying safe to attempt.
</details>

<details>
<summary>2. What specifically distinguishes a barcode scanner's keystrokes from a
person typing the same digits by hand?</summary>

Timing: a scanner emits each character with a very small, consistent gap (often
single-digit milliseconds), followed immediately by Enter — much faster and more
regular than real human typing, which is what a wedge detector's `maxGapMs` check is
built to tell apart.
</details>

<details>
<summary>3. Why does a crashed tab mid-scan still have the scan recorded, as long
as it made it into Dexie first?</summary>

Dexie (over IndexedDB) is a real, durable browser database — a write to it survives
a tab crash or reload, unlike data only held in a JavaScript variable. As long as
`enqueueScan` writes the entry *before* attempting the network call, a crash at any
point after that still leaves the pending entry intact for the next `flush()` to pick
up.
</details>

## 9. Words to know
- **Wedge scanner** — a barcode scanner that connects as a keyboard (a "keyboard
  wedge"), typing the scanned code's characters followed by Enter; detected by
  keystroke timing, not a special API.
- **Dexie** — a JavaScript wrapper around the browser's IndexedDB, giving it a
  simpler, Promise-based API.
- **Offline-first** — an app design where every action is written to a local store
  first and synced to the server opportunistically, so the UI never has to block on
  network availability.
- **Parked (floor sense)** — an outbox entry the flush gave up retrying
  automatically, surfaced to the person instead of silently retried forever.
