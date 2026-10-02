# Lesson 13.7 — A mock provider, and the switch to a real one

## 1. In one sentence
You'll define one adapter interface for an outside service (a shipping carrier), write
a deterministic mock that satisfies it with no network calls and no API key, write a
real provider behind the same interface, and pick between them automatically based on
whether a real key is configured.

## 2. Why it exists
InvAI talks to real outside services — carriers, marketplaces, suppliers, AI
providers — that cost real money per call, need real API keys that don't exist on a
development machine, and (in a marketplace sandbox) may simply not be approved yet.
If "run the app locally" required all of those, nobody could develop or test most of
the product. `CLAUDE.md` makes this an absolute rule: "No real API keys exist. Every
integration has a mock provider, chosen automatically when its key is missing, so the
platform works end to end locally. Never remove a mock."

The trick that makes this safe rather than a lie is the **interface**: both the mock
and the real provider implement the exact same TypeScript type. Code that calls
`carrierAdapter()` never knows or cares which one it got — which means the moment a
real key shows up, the switch is automatic and the calling code needs zero changes.

## 3. How it works

### Step 1 — the interface
```ts
// src/integrations/carrier/types.ts
export type Label = { trackingNumber: string; labelUrl: string; costCents: number };

export interface CarrierAdapter {
  buyLabel(input: { toZip: string; weightOz: number }): Promise<Label>;
}
```

### Step 2 — a deterministic mock
```ts
// src/integrations/carrier/mock.ts
import type { CarrierAdapter } from "./types";

export const mockCarrier: CarrierAdapter = {
  async buyLabel({ toZip, weightOz }) {
    // Deterministic: same input -> same output, every run, no network call.
    return {
      trackingNumber: `MOCK${toZip}${weightOz}`,
      labelUrl: "https://mock.local/label.pdf",
      costCents: 450 + weightOz * 10,
    };
  },
};
```
"Deterministic" matters more than it sounds: a mock that returns `Math.random()`
makes every test that depends on it flaky. Same input, same output, every time — so
a test failure means your code changed, not that the mock got unlucky.

### Step 3 — a real provider behind the same interface
```ts
// src/integrations/carrier/easypost.ts
import type { CarrierAdapter } from "./types";

export function easypostCarrier(apiKey: string): CarrierAdapter {
  return {
    async buyLabel({ toZip, weightOz }) {
      const res = await fetch("https://api.easypost.com/v2/shipments", {
        method: "POST",
        headers: { Authorization: `Bearer ${apiKey}` },
        body: JSON.stringify({ to_zip: toZip, weight_oz: weightOz }),
      });
      if (!res.ok) throw new Error(`EasyPost ${res.status}`);
      const data = await res.json();
      return { trackingNumber: data.tracking_code, labelUrl: data.label_url, costCents: Math.round(data.rate * 100) };
    },
  };
}
```

### Step 4 — the switch
```ts
// src/integrations/carrier/index.ts
import { env } from "../../env";
import { mockCarrier } from "./mock";
import { easypostCarrier } from "./easypost";

export function carrierAdapter() {
  const apiKey = process.env.EASYPOST_API_KEY;
  if (!apiKey) return mockCarrier;
  return easypostCarrier(apiKey);
}
```
Every caller writes `const carrier = carrierAdapter(); await carrier.buyLabel(...)` —
never `import { mockCarrier }` or `import { easypostCarrier }` directly.

### Step 5 — exercise both for real
```bash
unset EASYPOST_API_KEY
npx tsx -e 'import { carrierAdapter } from "./src/integrations/carrier"; carrierAdapter().buyLabel({ toZip: "90210", weightOz: 8 }).then(console.log)'
# -> { trackingNumber: "MOCK902108", ... } -- no network call happened
```
You won't have a real EasyPost key for this exercise — that's the point. Read the
real adapter's code (next section) instead of running it, and notice it's built from
*exactly* the same interface your mock satisfies.

## 4. In our code
- `invai-backend/src/integrations/carriers/types.ts` — the real `CarrierAdapter`
  interface your Step 1 modeled.
- `invai-backend/src/integrations/carriers/mock.ts` — the real `mockCarrier`:
  deterministic outputs derived from the input, no network, usable in every test and
  every local dev session with zero setup.
- `invai-backend/src/integrations/carriers/index.ts:15-29` — the real switch:
  `carrierAdapter(scope)` returns `mockCarrier` when `env.mocks.carrier` is true (no
  key) **or** when the company is a sample workspace (`tenancy.demo`) — "a sample
  workspace always gets the mock: it can never buy a real label" — a second,
  deliberate safety rule beyond just "no key."
- `invai-backend/src/integrations/carriers/easypost.ts` — the real provider, behind
  the same `CarrierAdapter` interface.
- `invai-backend/src/env.ts:279-335` (`mocks` block) — the real env-driven switch
  logic: `mocks.*` is computed as "true when the real key is missing," with a comment
  that a test run can never touch development data.
- Module 06.3 (`06-reliability/03-mocks-vs-real-providers.md`) — the full lesson,
  covering every mocked integration (carriers, suppliers, marketplaces, AI) and the
  `add-carrier-or-supplier-adapter`/`add-marketplace-integration` playbooks used when
  a real sandbox key actually arrives.

## 5. What it uses
- **The adapter pattern** — one interface, multiple implementations, selected by a
  single factory function — the general technique behind every "mock vs. real"
  switch in InvAI, not specific to any one library.
- **Environment variables as the switch key** — `env.ts` centralizes "is a real key
  configured," so the decision is made in one place, not re-derived with
  `process.env.X ? ... : ...` scattered through the codebase.

## 6. Try it yourself
1. Call `carrierAdapter().buyLabel(...)` with the same input twice and diff the two
   results — they should be byte-for-byte identical. Now change one field of the
   input (say, `weightOz`) and confirm the output changes in a way that still makes
   sense (the mock's cost formula should respond to it).
2. Read `invai-backend/src/integrations/carriers/index.ts:16-18` closely and answer:
   under what two different conditions does a company get `mockCarrier` even though
   `EASYPOST_API_KEY` is set? (Hint: look at `isSampleWorkspace`.)
3. Add a second method to your `CarrierAdapter` interface, `voidLabel`, implement it
   on both `mockCarrier` and `easypostCarrier`, and notice TypeScript immediately
   flags any adapter that's missing it — the interface is what makes "both
   implementations stay in sync" a compile-time guarantee, not a hope.

## 7. Common mistakes
- Writing a mock that calls `Math.random()` or `Date.now()` without seeding/freezing
  it. A test that passes or fails depending on *when* it happened to run is a flaky
  test, and flaky tests get ignored over time — which defeats the entire reason
  tests exist.
- Letting calling code import the mock or the real provider directly, instead of
  always going through the one switch function. The moment that happens, "switch to
  the real provider" stops being automatic — someone has to find and fix every direct
  import, which is exactly the kind of thing that gets missed under a deadline.
- Removing a mock once a real key exists, on the theory that it's "not needed
  anymore." `CLAUDE.md` is explicit: never remove a mock. Every teammate, every CI
  run, every future local session still needs to be able to run the whole platform
  with zero real keys.

## 8. Check yourself
<details>
<summary>1. Why does the mock need to be deterministic — same input always producing
the same output?</summary>

Because tests and local development depend on predictable behavior. A
non-deterministic mock makes any test built on top of it flaky — sometimes passing,
sometimes failing, with no code change in between — which erodes trust in the whole
test suite over time.
</details>

<details>
<summary>2. What's the actual mechanism that lets calling code stay unaware of
whether it's talking to the mock or the real provider?</summary>

Both implementations satisfy the exact same TypeScript interface (`CarrierAdapter`),
and all calling code only ever holds a reference typed as that interface, obtained
from one factory function (`carrierAdapter()`). The caller literally cannot tell
which concrete implementation it has without inspecting it at runtime — and nothing
in normal usage needs to.
</details>

<details>
<summary>3. Besides "no API key," what's a second, deliberate reason InvAI's real
carrier switch forces the mock even when a real key exists?</summary>

A sample/demo workspace (`tenancy.demo`) always gets the mock, regardless of whether
a real key is configured — a safety rule so a sample shop someone is exploring (or a
sales demo) can never accidentally spend real money buying a real shipping label.
</details>

## 9. Words to know
- **Adapter** — a concrete implementation of a shared interface for one specific
  provider (the mock, EasyPost, a specific marketplace), interchangeable with any
  other adapter of the same interface.
- **Deterministic** — producing the same output for the same input every time, with
  no randomness or dependence on the current time.
- **Sample/demo workspace** — a company flagged as a sample, which InvAI
  deliberately restricts from any real-money action regardless of configuration.
