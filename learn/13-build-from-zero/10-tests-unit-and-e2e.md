# Lesson 13.10 — Tests: unit tests, then E2E with Playwright

## 1. In one sentence
You'll write a plain Vitest unit test for pure logic (no database), a Vitest
acceptance test against a *real* Postgres database with real RLS turned on (proving
tenancy actually works, not just that a function returns the right value), and a
Playwright test that drives your whole stack — browser, backend, database — through
one real flow.

## 2. Why it exists
Not every behavior needs the same kind of test, and picking the wrong layer wastes
effort in both directions. A pure money-splitting function doesn't need a browser to
prove it rounds correctly — that's slow and tells you nothing a unit test couldn't.
But a unit test with a *mocked* database can't prove your lesson 13.4 RLS policy
actually blocks cross-tenant access — mocking the exact thing you need to test
proves nothing about whether it really works. InvAI's rule: pick the **lowest layer
that can actually prove the behavior**, and use `invai_test` — a real database, not
mocked — whenever tenancy, permissions, or anything DB-backed is in question.

## 3. How it works

### Step 1 — a unit test for pure logic
```ts
// src/pricing.ts
export function totalCents(items: { priceCents: number; qty: number }[]): number {
  return items.reduce((sum, i) => sum + i.priceCents * i.qty, 0);
}
```
```ts
// src/pricing.test.ts
import { describe, it, expect } from "vitest";
import { totalCents } from "./pricing";

describe("totalCents", () => {
  it("sums price * quantity across items", () => {
    expect(totalCents([{ priceCents: 500, qty: 2 }, { priceCents: 100, qty: 1 }])).toBe(1100);
  });
});
```
No database, no tenant, no network — just a function and its output.

### Step 2 — a tenant-scoped acceptance test against a real database
```ts
// src/widgets.acceptance.test.ts
import { describe, it, expect } from "vitest";
import { withTenant } from "./db/client";
import { createCompany } from "./test/fixtures";
import { createWidget, getWidget } from "./widgets/service";

describe("widgets", () => {
  it("AC1: a company can read a widget it created", async () => {
    const a = await createCompany();
    const widget = await withTenant(a.id, (tx) => createWidget(tx, a.id, { name: "T", priceCents: 500 }));
    const found = await withTenant(a.id, (tx) => getWidget(tx, widget.id));
    expect(found?.name).toBe("T");
  });

  it("AC2: a different company cannot read it — RLS, not an application check", async () => {
    const a = await createCompany();
    const b = await createCompany();
    const widget = await withTenant(a.id, (tx) => createWidget(tx, a.id, { name: "T", priceCents: 500 }));
    const found = await withTenant(b.id, (tx) => getWidget(tx, widget.id));
    expect(found).toBeUndefined(); // the row exists; company B's connection just can't see it
  });
});
```
Name each test after the exact behavior it proves (`"AC2: a different company
cannot read it"`) — a failing test name alone should tell you which specific
guarantee broke, with no need to read the test body first.

### Step 3 — red first
Run this test file **before** `getWidget`/`createWidget` exist, or before RLS is
turned on. It must fail for the right reason — a missing function, or AC2 actually
returning the row — not a typo or a missing import. A test that passes immediately,
before the behavior exists, is either wrong or testing something already true;
either way, that's worth knowing before you build, not after.

### Step 4 — an end-to-end test with Playwright
```bash
pnpm add -D @playwright/test
npx playwright install chromium
```
```ts
// e2e/create-widget.spec.ts
import { test, expect } from "@playwright/test";

test("owner can create a widget and see it in the list", async ({ page }) => {
  await page.goto("http://localhost:5173");
  await page.getByLabel("Name").fill("E2E Widget");
  await page.getByRole("button", { name: "Add" }).click();
  await expect(page.getByText("E2E Widget")).toBeVisible();
});
```
This test proves the layers actually connect — the browser really talks to your
backend, which really talks to Postgres, and the result really renders — something
no unit or acceptance test, each testing one layer in isolation, can prove by itself.

### Step 5 — run them, trimmed
```bash
npx vitest run --reporter=dot
npx playwright test --reporter=line
```
Trimming reporter output isn't just tidiness — on a large suite it's the difference
between a readable failure and a wall of text burying the one line that matters.

## 4. In our code
- `invai-backend/src/test/fixtures.ts:36-100, 162` — the real shared toolkit:
  `truncateAll`, `createCompany`, `createUser`, `createLocation`, `createStation`,
  `createConnection`, `createOrder`, `tenantContext` — your `createCompany()` call
  above is a tiny version of this.
- `invai-backend/src/modules/finance/profit.ts` — real pure logic (lesson 5.3) that
  gets a plain unit test, the same shape as your `totalCents` example — no database
  involved.
- `invai-backend/src/modules/ai/market.acceptance.test.ts` — a real
  `*.acceptance.test.ts` file, run against `invai_test` with real RLS, named by what
  it proves — exactly the pattern your Step 2 file followed.
- `invai-web/e2e/api-golden-path.spec.ts:55-454` — thirteen numbered, named
  Playwright tests, each one a step of the real golden path (import → map → gang
  sheet → floor → label → profit), each test's name describing the exact behavior it
  proves.
- `invai-backend/vitest.config.ts` — `fileParallelism: false` ("every test file
  shares one test database; run files one at a time") — a real, specific constraint
  your tiny setup doesn't need yet at this scale, but will the moment more than one
  test file touches the same database concurrently.
- Module 08.1 (`08-quality/01-tests-in-layers.md`) and 08.2 — the full lesson,
  including the "held-back case" rule: QA deliberately keeps 1–3 edge-case tests out
  of what the implementer sees, added only after they report a card done, to catch
  code written to pass exactly the visible tests and nothing more.

## 5. What it uses
- **Vitest** — the test runner for unit and acceptance tests across every InvAI
  TypeScript repo.
- **`invai_test`** — a real, separate Postgres database acceptance tests run
  against, with RLS genuinely enabled, so a tenancy bug shows up the same way it
  would in production — not hidden behind a mock.
- **Playwright** — drives a real browser against a real running stack for the E2E
  layer; module 08.2 covers its CI role in full.

## 6. Try it yourself
1. Delete the `WHERE`-equivalent (the RLS policy, or `withTenant`'s `set_config`
   call) from your lesson 13.4 setup, then re-run your Step 2 acceptance tests. AC2
   should fail — confirm it does, and read the failure message: does it clearly say
   "company B saw company A's widget," or something vaguer?
2. Comment out the `priceCents` field from your `totalCents` unit test's assertion
   and watch it still pass — a reminder that a test only proves what it actually
   asserts, not everything the function does.
3. Run your Playwright test with a backend that isn't running at all. Read the
   failure — is it obvious from the output that the *backend* is the problem, or
   does it look like a frontend bug? This is why E2E failures need triage (the real
   `qa-engineer` role's job is exactly this: root-causing which layer actually broke).

## 7. Common mistakes
- Writing a unit test (mocked database) for something that's fundamentally about
  RLS or permissions. A mock can be told to return `true` or `false` on command — it
  can't tell you whether a real database policy actually enforces the boundary you
  think it does.
- Treating an immediately-green test (written before the feature exists) as a good
  sign. It almost always means the test isn't exercising the new behavior at all, or
  the behavior was already true — either way worth knowing before, not after,
  building starts.
- Naming tests generically (`"it works"`, `"test 1"`) instead of after the specific
  behavior being proven. A failure in a vaguely-named test tells you something broke
  somewhere in the file; a failure in `"AC2: a different company cannot read it"`
  tells you exactly what broke.

## 8. Check yourself
<details>
<summary>1. Why can't a unit test with a mocked database prove that RLS actually
isolates two tenants?</summary>

A mock returns whatever the test tells it to return — it has no real RLS policy to
enforce or fail to enforce. Proving real isolation requires a real database
connection, with the real policy active, actually being queried under two different
tenant settings — that's what the acceptance-test layer, against `invai_test`, is
specifically for.
</details>

<details>
<summary>2. A new test passes immediately, before any new code was written for the
feature it's supposed to prove. What does that most likely mean?</summary>

Either the test isn't actually exercising the new behavior (it's testing something
else, or asserting too little), or the behavior it's checking was already true
before this change. Either way, it's not proof the new feature is done — it's a
signal to double-check the test itself.
</details>

<details>
<summary>3. What does an end-to-end test prove that a unit test and an acceptance
test, even together, cannot?</summary>

That the layers actually connect in practice — that a real browser's request
reaches the real backend, which reaches the real database, and the result actually
renders back correctly. Unit and acceptance tests each prove one layer works in
isolation; only an E2E test exercises the full path between them.
</details>

## 9. Words to know
- **Unit test** — tests a pure function's logic in isolation, no database, no
  network.
- **Acceptance test (InvAI sense)** — a Vitest test against a real `invai_test`
  database, through real tenant fixtures, proving one specific behavior.
- **E2E (end-to-end) test** — a Playwright test driving a real flow across the
  whole stack, proving the layers actually connect.
- **Fixture** — a reusable test helper (`createCompany`, `createOrder`, ...) that
  builds a realistic starting state without each test reinventing it.
- **Red first** — writing a test before the behavior exists, and confirming it
  fails for the right reason, so passing later is real proof.
