# Lesson 13.5 — Auth and roles with Better Auth

## 1. In one sentence
You'll add email/password sign-in with Better Auth, model each company as an
"organization" with members who carry a role, and write a permission guard that
checks a procedure's declared permission against the signed-in member's role before
any handler runs.

## 2. Why it exists
Two separate questions hide inside "is this request allowed?" — **who is this**
(authentication: do I believe you're the person this session says you are) and
**what can they do** (authorization: does an office person get to buy a shipping
label, or only an owner?). InvAI's answer: Better Auth owns the first question
entirely — sessions, cookies, password hashing, email verification — and the oRPC
contract's `permission` metadata (lesson 13.2) plus a backend guard owns the second.
Mixing the two into ad-hoc `if (user.role === "owner" || user.role === "admin")`
checks scattered across handlers is how a shop's presser ends up able to delete
orders because someone forgot one `if`.

Better Auth's **organization** plugin is the natural fit for "one person can belong
to more than one shop" (a vendor working with several print shops, or someone who
owns two locations under separate accounts) — each company is an organization, each
person's membership in it carries one InvAI-specific role.

## 3. How it works

### Step 1 — install and configure
```bash
cd ~/invai-from-zero/backend
pnpm add better-auth
```
`src/auth.ts`:
```ts
import { betterAuth } from "better-auth";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { organization } from "better-auth/plugins";
import { db } from "./db/client";
import { users, sessions, accounts, verifications, companies, members } from "./db/schema";

export const auth = betterAuth({
  appName: "FromZero",
  database: drizzleAdapter(db, {
    provider: "pg",
    schema: { users, sessions, accounts, verifications, companies, members },
  }),
  secret: process.env.AUTH_SECRET!,
  emailAndPassword: { enabled: true, minPasswordLength: 8 },
  plugins: [organization()],
});
```
Better Auth needs its own tables (`users`, `sessions`, `accounts`, `verifications`,
plus the organization plugin's `companies`/`members`) — generate and run that
migration the same way you did in lesson 13.3.

### Step 2 — roles, as your own concept
Better Auth's organization plugin has its own access-control layer, but InvAI
deliberately keeps that for Better Auth's *own* endpoints only (invite, remove
member) and defines its own role/permission model on top, in the contract package:
```ts
// contracts: src/roles.ts
export const ROLES = ["owner", "admin", "office", "presser"] as const;
export type Role = (typeof ROLES)[number];

export const ROLE_PERMISSIONS: Record<Role, string[]> = {
  owner: ["widgets.read", "widgets.write"],
  admin: ["widgets.read", "widgets.write"],
  office: ["widgets.read"],
  presser: [],
};
```
A member's `role` column (free text on the `members` table, your own addition) holds
one of `ROLES`; `ROLE_PERMISSIONS[role]` is the single place that decides what each
role can do.

### Step 3 — the permission guard
```ts
import { os } from "@orpc/server";
import { ROLE_PERMISSIONS } from "@invai/contracts";
import { auth } from "./auth";

const authed = os.use(async ({ context, next, procedure }) => {
  const session = await auth.api.getSession({ headers: context.headers });
  if (!session) throw new Error("UNAUTHORIZED");

  const meta = procedure["~orpc"].meta as { permission: string };
  const role = session.member.role as keyof typeof ROLE_PERMISSIONS;
  if (meta.permission !== "none" && !ROLE_PERMISSIONS[role].includes(meta.permission)) {
    throw new Error(`FORBIDDEN: missing ${meta.permission}`);
  }
  return next({ context: { ...context, companyId: session.session.activeOrganizationId, role } });
});
```
This middleware runs for *every* procedure built from `authed`, so no handler can
forget the check — it's structural, not something each author has to remember to
add.

### Step 4 — exercise it for real
```bash
curl -s -c cookies.txt -X POST localhost:3100/api/auth/sign-up/email \
  -H 'content-type: application/json' \
  -d '{"email":"owner@test.local","password":"testtest","name":"Owner"}'
curl -s -b cookies.txt -X POST localhost:3100/rpc/widgets/create \
  -d '{"name":"Test","priceCents":500}'     # -> works, owner has widgets.write
# Now sign in as a presser-role member instead and repeat — expect FORBIDDEN.
```

## 4. In our code
- `invai-backend/src/auth.ts:152-171` — the real `authOptions`: a `drizzleAdapter`
  over the real schema tables, `emailAndPassword` with `requireEmailVerification:
  false` ("unverified users can sign in; only paid actions need a verified email" —
  a deliberate, commented product decision), and `plugins: [organization(), ...]`.
- `invai-contracts/src/roles.ts:6-16` — the real `ROLES` tuple (`owner`, `admin`,
  `office`, `designer`, `presser`, `packer`, `receiver`, `vendor`) and the comment
  explaining vendor organizations only ever have the `vendor` role.
- `invai-backend/src/api/orpc.ts:103-130` — the real guard middleware: it switches
  on `auth: "user" | "floor" | "station" | "public"` from the procedure's meta
  *before* checking permission at all (a floor tablet needs a different kind of
  session than a browser), then the same `context.permissions.has(meta.permission)`
  check your Step 3 wrote by hand.
- `invai-backend/src/api/orpc.ts:40-48` — `EMAIL_VERIFIED_PROCEDURES`, a second,
  separate check layered on top of the permission check for money-moving procedures
  specifically (label buys, Stripe checkout) — proof that "authenticated" and
  "authorized" and "verified enough for this specific action" are three different
  questions InvAI answers separately, not one blob of `if`s.
- Module 09.1 (`09-security/01-auth-and-roles.md`) — the full lesson on this topic,
  including the floor PIN login flow (lesson 13.9 touches this from the floor app's
  side) and the full permission matrix test.

## 5. What it uses
- **Better Auth** — a TypeScript auth library handling sessions, password hashing
  and email flows, with an `organization` plugin InvAI maps onto "company"; module
  03.3 covers why this over rolling auth by hand or a heavier identity provider.
- **oRPC middleware (`os.use(...)`)** — the mechanism that lets a check run for
  every procedure built from a given base builder, instead of being copy-pasted into
  each handler.

## 6. Try it yourself
1. Sign in as your `presser` member and call `widgets.create` directly — confirm
   you get `FORBIDDEN`, then check the *exact* permission string in the error
   against `ROLE_PERMISSIONS.presser` to see why.
2. `grep -n "sessionKind\|auth: \"floor\"\|auth: \"station\"" invai-backend/src/api/orpc.ts`
   and read the three-way switch. Why might a floor tablet need a different
   `auth` mode than a browser session, even though both are "a signed-in person"?
3. Open `invai-contracts/src/roles.ts` and find `SHOP_ROLES` vs. the roles that log
   in with a station PIN. Why would a vendor organization's single role (`vendor`)
   never appear in that PIN-login list?

## 7. Common mistakes
- Checking permissions with scattered `if (role === "owner")` calls inside handlers
  instead of one guard every procedure passes through. It's easy to forget one
  handler; a structural middleware can't be forgotten because nothing reaches a
  handler without going through it first.
- Treating "has a valid session" as the same thing as "is allowed to do this." A
  signed-in presser is a real, authenticated user — and still should get `FORBIDDEN`
  for `widgets.write`. Authentication and authorization are different checks, and
  skipping the second because the first passed is a real way to leak write access.
- Reusing Better Auth's own organization access-control (meant for its own invite/
  remove-member endpoints) as if it were your application's permission system. InvAI
  deliberately keeps those separate — the contract's own `ROLE_PERMISSIONS` is the
  one place application permissions are decided.

## 8. Check yourself
<details>
<summary>1. What's the difference between authentication and authorization, and
which one does Better Auth itself handle?</summary>

Authentication answers "who is making this request" (a valid session, a real
password match); authorization answers "is this specific person allowed to do this
specific thing." Better Auth handles authentication (sessions, passwords, email
flows); InvAI's own permission guard, reading `ROLE_PERMISSIONS` from the contract,
handles authorization.
</details>

<details>
<summary>2. Why is the permission check written as middleware that every
<code>authed</code> procedure passes through, rather than a line added inside each
handler?</summary>

A middleware can't be skipped by accident — every procedure built from the guarded
base builder goes through it before its handler ever runs. A per-handler check
depends on every author remembering to add it correctly every time, which is exactly
the kind of thing that gets missed under time pressure.
</details>

<details>
<summary>3. A procedure's contract meta says <code>permission: "none"</code>. Does
that mean anyone, signed in or not, can call it?</summary>

No — `permission: "none"` only skips the *permission* check; the `auth` mode (user,
floor, station, or public) on the same meta still applies. A procedure can require a
real signed-in session (`auth: "user"`) while needing no specific permission beyond
that, which is exactly `me.get`'s real shape in InvAI's contract.
</details>

## 9. Words to know
- **Authentication** — proving who is making a request (a valid session).
- **Authorization** — deciding what a known, authenticated requester is allowed to
  do.
- **Organization (Better Auth)** — Better Auth's grouping concept; InvAI maps one
  organization to one company (shop or vendor).
- **Member** — a person's relationship to one organization, carrying InvAI's own
  `role` column.
- **Permission guard** — the middleware that checks a procedure's declared
  permission against the signed-in member's role before any handler runs.
