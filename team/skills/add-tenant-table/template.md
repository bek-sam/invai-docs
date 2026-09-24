# Tenant table template

Adapt names. Check drizzle APIs in `invai-backend/node_modules/drizzle-orm/pg-core` (drizzle 0.45 is newer than training data).

## Schema (`src/db/schema/<area>.ts`)

```ts
import { foreignKey, index, integer, pgTable, text, uniqueIndex, uuid } from "drizzle-orm/pg-core";
import { enumText, id, tenantPolicy, timestamps } from "./_shared";
import { companyId } from "./tenancy";
import { orders } from "./orders";

export const PRINT_NOTE_KINDS = ["reminder", "defect"] as const;

/** One line of doc comment: what a row is, in shop words. */
export const printNotes = pgTable(
  "print_notes",
  {
    id: id(),
    companyId: companyId(),
    orderId: uuid().notNull(),
    kind: text(enumText(PRINT_NOTE_KINDS)).notNull().default("reminder"),
    /** Natural key for idempotent upserts (e.g. the source event id). */
    sourceKey: text().notNull(),
    costCents: integer().notNull().default(0),
    ...timestamps,
  },
  (t) => [
    // S-26: the FK carries company_id, so it cannot point at another company's order.
    // Needs uniqueIndex().on(orders.companyId, orders.id) on the parent.
    foreignKey({
      columns: [t.companyId, t.orderId],
      foreignColumns: [orders.companyId, orders.id],
    }).onDelete("cascade"),
    uniqueIndex().on(t.companyId, t.sourceKey),
    index().on(t.companyId, t.orderId),
    tenantPolicy("print_notes"),
  ],
).enableRLS();
```

If the parent has no `(company_id, id)` unique index yet, adding it is a change to another module's table: ask its owner (and `zero-downtime-migration` if the table is large). Until then, use a single-column FK and validate the parent in the service:

```ts
const [order] = await tx.select({ id: orders.id }).from(orders).where(eq(orders.id, input.orderId));
if (!order) throw notFound("order", input.orderId); // RLS hides other companies' rows
```

(Reading another module's table is only allowed through its service: call `getOrder` from `modules/orders/service.ts` rather than querying `orders` yourself.)

## Tests (`src/modules/<area>/<area>.test.ts`)

```ts
import { describe, expect, it } from "vitest";
import { withTenant } from "../../db/client";
import { printNotes } from "../../db/schema";
import { createCompany, createConnection, createOrder } from "../../test/fixtures";

describe("print_notes tenant isolation", () => {
  it("company B cannot see company A's rows", async () => {
    const a = (await createCompany()).id;
    const b = (await createCompany()).id;
    const { order } = await createOrder(a, (await createConnection(a)).id);
    await withTenant(a, (tx) =>
      tx.insert(printNotes).values({ companyId: a, orderId: order.id, sourceKey: "k1" }),
    );
    expect(await withTenant(b, (tx) => tx.select().from(printNotes))).toHaveLength(0);
  });

  it("company B cannot attach a row to company A's order", async () => {
    const a = (await createCompany()).id;
    const b = (await createCompany()).id;
    const { order } = await createOrder(a, (await createConnection(a)).id);
    await expect(
      withTenant(b, (tx) =>
        tx.insert(printNotes).values({ companyId: b, orderId: order.id, sourceKey: "k2" }),
      ),
    ).rejects.toThrow(); // composite FK violation
  });

  it("the wrong companyId fails the RLS WITH CHECK", async () => {
    const a = (await createCompany()).id;
    const b = (await createCompany()).id;
    const { order } = await createOrder(a, (await createConnection(a)).id);
    await expect(
      withTenant(b, (tx) =>
        tx.insert(printNotes).values({ companyId: a, orderId: order.id, sourceKey: "k3" }),
      ),
    ).rejects.toThrow();
  });
});
```

Check the return shape of `createOrder` in `src/test/fixtures.ts` before copying (it returns the order and its items). Add a service-level test too: `svc.getX(tx, ctxB, idFromA)` throws `NOT_FOUND`.
