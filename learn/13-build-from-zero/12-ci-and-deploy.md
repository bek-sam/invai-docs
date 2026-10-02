# Lesson 13.12 — CI on GitHub Actions, and a deploy outline with SST and its costs

## 1. In one sentence
You'll write a GitHub Actions workflow that spins up real Postgres and Valkey
services, runs `typecheck`/`lint`/`test` on every push, and read (without deploying)
a minimal SST config describing what AWS resources a real deploy would create — plus
how to price them before anything actually runs.

## 2. Why it exists
"Tests pass on my machine" is not the same claim as "tests pass," full stop — your
machine has state (a database with leftover rows, environment variables you set
once and forgot about) that CI deliberately starts without. CI's job is to prove the
same thing a fresh clone, with nothing assumed, would prove. `CLAUDE.md`'s definition
of done requires `pnpm typecheck && pnpm lint && pnpm test` passing "in every repo
you touched" — CI is what checks that claim mechanically, on every push, instead of
trusting it.

SST (on top of this) is "infrastructure as code" for AWS: instead of clicking
through the AWS console to create a database, a queue, and a container service by
hand (and nobody remembering exactly what was clicked six months later), the whole
shape of production is a TypeScript file, reviewable like any other code change.
This lesson stops short of an actual `sst deploy` — reading and pricing the config is
the real exercise; the real project's own SST file hasn't been deployed yet either
(see "In our code" below), and a real deploy needs the owner's explicit go-ahead.

## 3. How it works

### Step 1 — a minimal CI workflow
```yaml
# .github/workflows/ci.yml
name: CI
on: { push: { branches: [main] }, pull_request: {} }
permissions: { contents: read }

jobs:
  check:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg17
        env: { POSTGRES_USER: fz, POSTGRES_PASSWORD: fz, POSTGRES_DB: fz }
        ports: ["5432:5432"]
        options: --health-cmd "pg_isready -U fz -d fz" --health-interval 5s --health-retries 10
      valkey:
        image: valkey/valkey:8
        ports: ["6379:6379"]
    env:
      DATABASE_URL: postgres://fz:fz@localhost:5432/fz
      REDIS_URL: redis://localhost:6379
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version: 24, cache: pnpm }
      - run: pnpm install --frozen-lockfile
      - run: pnpm lint
      - run: pnpm typecheck
      - run: pnpm test
```
This is a real, runnable workflow — the services block gives you an actual Postgres
and Valkey for the duration of the job, the same services lesson 13.1's compose file
gave you locally, just started fresh for every run.

### Step 2 — pin your third-party actions
```yaml
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4
```
A version tag like `@v4` can be force-moved to point at different code later (by the
action's maintainer, or — in a supply-chain attack — by someone who compromised
their account). Pinning the exact commit SHA, with the human-readable tag kept only
as a trailing comment, means "what actually runs in your CI" can't silently change
underneath you.

### Step 3 — a minimal SST config (read it, don't deploy it)
```ts
// sst.config.ts
export default $config({
  app(input) {
    return { name: "fromzero", home: "aws", removal: input?.stage === "production" ? "retain" : "remove" };
  },
  async run() {
    const vpc = new sst.aws.Vpc("Vpc", { nat: "ec2" });
    const db = new sst.aws.Postgres("Db", { vpc });
    const api = new sst.aws.Service("Api", { cluster: new sst.aws.Cluster("Cluster", { vpc }), link: [db] });
    return { apiUrl: api.url };
  },
});
```
`removal: "retain"` on production (and `"remove"` everywhere else) is a real,
deliberate safety detail: a `staging` stage can be torn down freely; production
resources survive even an accidental `sst remove`.

### Step 4 — price it before deploying anything
Before ever running `sst deploy`, list every resource the config would create (a
VPC with NAT gateways, an RDS instance, an ECS service, ...) and look up each one's
current on-demand list price. This read-only exercise is exactly what InvAI's own
cost estimate does: "no `aws` or `sst` command was run, nothing was deployed... every
price is a current public list price with its source and fetch date."

## 4. In our code
- `invai-backend/.github/workflows/ci.yml:17-39` — the real services block: the
  exact `pgvector/pgvector` and `valkey/valkey` images, pinned **by digest**
  (`@sha256:...`, with the human-readable version as a trailing comment) rather than
  by tag — one step stricter than the SHA-pinned actions below, and worth noticing
  the difference.
- `invai-backend/.github/workflows/ci.yml:60-88` — the real checkout/setup/install
  steps, every third-party action pinned to a full commit SHA
  (`actions/checkout@11d5960a...# v4`) — the exact pattern Step 2 above explained,
  taken from a real, running workflow.
- `invai-backend/.github/workflows/ci.yml:85-100` — a real step creating the
  `invai_app` role and extensions inline, with the comment "mirrors
  invai-infra/local/init.sql" — CI doesn't have that file checked out, so it
  reproduces the same SQL rather than silently drifting from it.
- `invai-infra/sst.config.ts:1-30` — the real config: stages `production`,
  `staging`, `demo` (the only stage allowed to boot on mock providers), `removal:
  input?.stage === "production" ? "retain" : "remove"`, and `protect: input?.stage
  === "production"` — a second, independent safety layer on top of `removal`.
- `invai-docs/ops/cost-estimate-aws.md:1-25` — the real, read-only cost exercise:
  "Config version... 5 commits ahead of origin/main — unpushed," every resource
  priced from the config as it exists on disk, every price dated and sourced, "no
  `aws` or `sst` command was run, nothing was deployed."
- `CLAUDE.md` ("The owner's rules") and the `.claude/hooks/guard-bash.py` guard — the
  real rule this lesson respects by never actually deploying: `aws` commands and
  deploys are blocked by a hook, and anything outbound, irreversible, costly or risky
  goes to the owner first.

## 5. What it uses
- **GitHub Actions** — runs your CI workflow on every push/PR, with `services:`
  giving you real, disposable Postgres/Valkey containers for the job's lifetime.
- **SST (v3, on AWS)** — infrastructure-as-code: the shape of production AWS
  resources, written in TypeScript, reviewable and typecheckable like any other code
  change; module 03.5 and module 11.1 cover why this over hand-clicking the AWS
  console or raw Terraform/CloudFormation.
- **Pinning by SHA/digest** — the supply-chain-security practice of referencing an
  exact commit or image digest instead of a mutable tag, so "what runs" can't change
  without a new, reviewable line in your workflow file.

## 6. Try it yourself
1. Deliberately break `pnpm typecheck` in a tiny way (an unused import with `noUnusedLocals`
   on, say) and push it — or just run the workflow's steps locally in order — and
   confirm CI would catch it before `pnpm test` ever runs. Why run `lint`/`typecheck`
   *before* the slower test step rather than after?
2. Read `invai-docs/ops/cost-estimate-aws.md`'s resource table and pick one line
   (say, the NAT gateways). Look up its current AWS list price yourself and compare
   it to what the doc states — is it still accurate, or has AWS's pricing moved since
   the doc's "fetched" date?
3. In your own `sst.config.ts`, change `removal` to always be `"remove"` (even for
   `production`) and explain, in one sentence, the real-world consequence of an
   accidental `sst remove --stage production` under that config versus the original.

## 7. Common mistakes
- Referencing third-party GitHub Actions by a mutable tag (`@v4`) instead of a
  pinned commit SHA. A tag can be moved by its maintainer (or an attacker who
  compromises their account) to point at different, possibly malicious code, with no
  change visible in your own repository's history.
- Running `sst deploy` (or any `aws` command) to "just see what happens," without
  the owner's explicit go-ahead on a real project. This project's guard hook blocks
  `aws` commands and deploys outright, and the cost-estimate exercise exists
  specifically so a deploy's actual cost and shape are understood *before* anyone
  runs it for real.
- Writing a cost estimate from memory or a rough guess instead of real, dated,
  sourced prices. "Actual bills will differ" is expected and stated up front in
  InvAI's own estimate — what's not acceptable is a number nobody could trace back to
  a real price list on a real date.

## 8. Check yourself
<details>
<summary>1. Why does CI create its own Postgres/Valkey containers from scratch on
every run, instead of connecting to a persistent shared database?</summary>

So every CI run proves the same thing a brand-new clone, with nothing assumed,
would prove — no leftover rows, no environment drift, no "it only passes because of
state someone left behind." It's the mechanical version of "works on a fresh
checkout," not "works on my machine right now."
</details>

<details>
<summary>2. What's the actual risk pinning a GitHub Action to a commit SHA protects
against, that pinning to a version tag (<code>@v4</code>) does not?</summary>

A tag is a pointer that can be moved to a different commit later — by the
maintainer, or by an attacker who compromises their account or repository. A commit
SHA is immutable: `actions/checkout@11d5960a...` always refers to that exact code,
forever, so your workflow can't silently start running different code without a
visible change to your own file.
</details>

<details>
<summary>3. Why does InvAI's real cost estimate explicitly state "no <code>aws</code>
or <code>sst</code> command was run, nothing was deployed"?</summary>

Because the whole exercise is meant to answer "what would this cost, and is it
reasonable" *before* committing to spend any real money — reading the config and
pricing its resources from public list prices lets the owner make that decision with
real numbers, without the risk, cost or irreversibility of an actual deploy.
</details>

## 9. Words to know
- **CI (continuous integration)** — automatically running checks (typecheck, lint,
  tests) on every push, against a fresh environment, to prove a change is sound
  independent of any one developer's machine state.
- **SST** — an infrastructure-as-code framework for deploying to AWS from
  TypeScript config; InvAI's production shape is a reviewable `sst.config.ts`, not
  manual console clicks.
- **Pinning (by SHA/digest)** — referencing an exact, immutable commit or image
  identifier instead of a mutable tag, so what actually runs can't change
  silently.
- **Stage (SST)** — a named deploy target (`production`, `staging`, `demo`, ...),
  each potentially with different safety settings (like `removal`/`protect`).
