# InvAI agent team: gap analysis, final roster, skills and operating system

As of Sep 24, 2026. Scope: the 16 Claude Code subagents in `invai/.claude/agents/`, the handbook `invai/CLAUDE.md`, `build/v1-plan.md`, `00-platform-concept.md`, and research files 02 and 03. It also checks the owner's proposed rules against published guidance on multi-agent coding.

**Summary.**
- The current team is strong on building: contract, backend, imaging, web, floor and integrations are all covered well.
- It is weak in five areas:
  1. **Independence.** The people who build are also the ones who verify.
  2. **Enforcement.** Every rule is prose, with no hook, tool limit or owned-path check behind it.
  3. **Running a live service.** No one owns observability, incidents or on-call.
  4. **Everything after the code.** Support, growth, marketplace approvals, legal drafts and metrics have no owner.
  5. **Written memory.** There are no ADRs, no scope file, no lessons file, and several docs that role files point to don't exist yet.
- The proposed roster has **20 roles**:
  - Keep 12 roles, sometimes with a narrower charter.
  - Merge 1: the design-system engineer goes into the product designer.
  - Rename and widen 3: devops becomes platform-sre, pilot-success becomes customer-success, tech-writer becomes docs-writer.
  - Add 5: an independent reviewer, an AI engineer, a data analyst, a compliance officer and a growth marketer.
  - Three of the new roles start only when a trigger event happens, so the number of agents running at once stays at 3–5.
- About 45 named playbooks go into `.claude/skills/`. Nine of them are shared by every role.

---

## 1. What a complete early-stage B2B SaaS team covers, and what AI agents can do

For a small B2B SaaS, the usual advice is:
- Founder-led sales until about 10–20 customers.
- Onboarding, support and customer success blur together early on.
- "Hire customer success before you hire product managers. Keeping the customers you have beats shipping features nobody asked for."

Sources: [Cerebral Ops, first 10 hires](https://blog.cerebralops.in/first-10-hires-saas-startup-sequence/), [Seaport Search on first CS leaders](https://www.seaportsearchpartners.com/blog/hiring-your-first-customer-success-leader-what-founders-of-b2b-saas-startups-need-to-know), [Activated Scale on the first sales hire](https://www.activatedscale.com/feeds/blog/first-sales-hire-b2b-saas).

InvAI has three things most SaaS companies don't:
- **Marketplace gatekeepers.** Etsy commercial access, Amazon's SP-API Data Protection Policy, Shopify App Store review, TikTok Partner Center and the Walmart Solution Provider program.
- **A physical floor.** A software bug here means a wrong shirt gets pressed.
- **A wide customer range.** Customers run from a one-person Etsy shop to a multi-location shop doing more than 1,000 orders a day.

Column key for the table below:
- **Covered now** means a current role owns the function.
- **AI can do** means work an agent can finish and verify on its own.
- **Owner must** means the human founder has to do it: legal authority, money, relationships, or physical-world facts.

| Function | What it covers at InvAI's stage | Covered now | AI can do | Owner must |
|---|---|---|---|---|
| Product management | Scope, specs, prioritization, pricing hypothesis, keep/cut log | Yes (product-manager) | Specs, scoring, backlog, research synthesis, pricing analysis | Final scope and price calls; customer interviews (Reddit and Facebook voice was unreachable in research 03) |
| Design / UX | Flows, UX audits, design system, UX copy, accessibility | Yes (product-designer, design-system-engineer) | Audits with screenshots, specs, components, WCAG checks | Watching real pressers use the tablet on a real floor |
| Engineering | Contract, backend, imaging, web, floor, integrations | Yes (8 roles) | Nearly all of it | Picking between business trade-offs the agents surface |
| AI / ML quality | Prompts, model choice, evals, cost per tenant, refusal handling | **No.** v1-plan says "only for bulk routes after an eval shows equal quality", but no role owns evals | Eval sets, regression runs, cost tracking | Accepting the risk on trademark-check misses |
| Platform / SRE | Deploys, observability, SLOs, incidents, backups, cost | Partly (devops: infra and CI only; no logs, alerts or on-call) | IaC, dashboards, alert rules, runbooks, restore drills | Cloud account, spend, every production deploy go-ahead (devops rule 1), being paged |
| Security | Threat models, RLS, PII, SP-API readiness | Yes (security-reviewer) | Reviews, tests, evidence packs | Hiring a pen tester, signing attestations, notifying Amazon within 24 h |
| QA | E2E suites, release verification, cross-repo bugs | Yes (qa-engineer) | All of it | Final acceptance on real shop data |
| Code review | Independent review of every change | **No dedicated role.** The tech lead reviews "every report", and QA and security fix their own findings | Fresh-context, read-only review | None |
| Data / analytics | Metric definitions, product analytics, pilot KPIs, unit economics, experiment readouts | **No.** Nothing is instrumented; `tools-stack.md` plans PostHog, and no code uses it | Event taxonomy, SQL, dashboards, weekly reviews | Choosing the few metrics that decide the company |
| Integrations / partnerships | Adapters (engineering), partner programs, API approvals | Engineering yes; approvals only as "what still needs a human" | Application packets, questionnaires, doc research | Submitting applications, holding partner accounts, negotiating EasyPost rates |
| Marketplace and privacy compliance | Etsy Creativity Standards, AI disclosure, GDPR webhooks, DPP, privacy policy, ToS, DPA | **No** (bits spread across integrations and security) | Drafts, checklists, policy-change watch, evidence | Lawyer review, signing, accepting marketplace terms |
| Growth / marketing | Positioning, website, SEO comparison pages, app-store listings, lifecycle email, launch | **No.** There isn't even a public site: `invai-web/src/routes` has only login, signup and the app | Copy, pages, email sequences, SEO audits, listing text | Brand voice approval, ad spend, community presence, anything sent under the founder's name |
| Sales / onboarding | Demos, trials, pilot onboarding, go-live | Onboarding yes (pilot-success); sales no | Demo scripts, onboarding runbooks, dry-run imports, ROI numbers | Every sales conversation and contract |
| Support / success | Tickets, help center, churn signals, feedback loop | Pilot feedback only | Triage, macros, help articles, bug reproduction, churn review | Replying to customers (the current rule: "never contact a shop") |
| Finance / pricing | Plans, per-label margin, AI and infra cost, Stripe | Only as a PM "pricing hypothesis"; Stripe is stubbed | Unit-economics models, cost reports, billing code | Bank, Stripe account, tax, what to charge |
| Legal | Terms, privacy, DPA, AI and IP positions | **No** | First drafts and checklists only | A lawyer's review; every signature |
| Docs | Dev docs, runbook, demo guide, user help, release notes | Yes (tech-writer); user help only in passing | All of it | None |

**The takeaway.** Agents can do almost all of the production work in each function. The owner keeps four kinds of work:
- **Authority:** signing, submitting applications, spending, deploying to production.
- **Relationships:** sales, customer replies, partners.
- **Ground truth:** real shop floors, real customer interviews.
- **Final judgment:** scope, price, and accepting risk.

The team's job is to shrink each of those to a one-page decision with a recommendation (see section 5.5).

---

## 2. Best practice for multi-agent AI coding teams

### 2.1 What Anthropic's guidance says

1. **Start simple, and add agents only when parallelism pays for itself.**
   - "Finding the simplest solution possible, and only increasing complexity when needed" ([Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)).
   - Multi-agent systems use about 15× the tokens of a chat, against about 4× for a single agent ([How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)).
   - The agent-teams docs say to start with 3–5 teammates, that "three focused teammates often outperform five scattered ones", and suggest 5–6 tasks per teammate ([Agent teams](https://code.claude.com/docs/en/agent-teams)).
   - InvAI's own lesson ("keep 3–4 agents running at once") already matches this.
2. **Delegate with an objective, an output format, tools and boundaries.**
   - "Each subagent needs an objective, an output format, guidance on the tools and sources to use, and clear task boundaries". Without them, agents duplicate work or misread the task ([multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)).
   - The tech-lead role's "Writing an assignment" section already does this. It should become a template that a hook checks (section 5.2).
3. **Context is a finite budget.**
   - Aim for "the smallest possible set of high-signal tokens". Use sub-agents that return "a condensed, distilled summary", just-in-time retrieval, and structured notes kept outside the context window ([Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)).
   - The Claude Code docs warn that "bloated CLAUDE.md files cause Claude to ignore your actual instructions". Move occasional knowledge into skills, which load on demand ([Best practices](https://code.claude.com/docs/en/best-practices), [Skills](https://code.claude.com/docs/en/skills)).
   - InvAI's role files already copy long "how it works" sections. Those belong in repo READMEs or skills, not in every agent's prompt.
4. **Give agents a check they can run, and make it deterministic.**
   - "Claude stops when the work looks done. Without a check it can run, 'looks done' is the only signal available."
   - Hooks "are deterministic and guarantee the action happens", while CLAUDE.md is "advisory".
   - Agent teams provide `TaskCreated`, `TaskCompleted` and `TeammateIdle` hooks that can block with exit code 2 ([Best practices](https://code.claude.com/docs/en/best-practices), [Agent teams](https://code.claude.com/docs/en/agent-teams)).
5. **Separate the writer from the reviewer.**
   - "A fresh context improves code review since Claude won't be biased toward code it just wrote."
   - An adversarial reviewer "sees only the diff and the criteria you give it, not the reasoning that produced the change".
   - The docs also warn: "a reviewer prompted to find gaps will usually report some, even when the work is sound". Tell reviewers to flag only gaps that affect correctness or the stated requirements ([Best practices](https://code.claude.com/docs/en/best-practices)).
6. **Explore, then plan, then code; keep each unit small.**
   - Long-running agent work went well only when "asked to work on only one feature at a time".
   - A feature list that starts with every item marked "failing" (kept in JSON, because models are less likely to edit it by accident) stops agents "declaring victory prematurely" ([Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)).
7. **Limit each agent's tools to its job.**
   - Subagent frontmatter supports `tools`, `disallowedTools`, `permissionMode`, `skills` (preloaded), `memory: project` (persistent per-agent notes under `.claude/agent-memory/<name>/`) and `maxTurns` ([Subagents](https://code.claude.com/docs/en/sub-agents)).
   - None of InvAI's 16 files uses any of these. Every agent can edit every file.
8. **Watch the lead.**
   - "Sometimes the lead starts implementing tasks itself instead of waiting for teammates", and "the lead can stop early too" ([Agent teams](https://code.claude.com/docs/en/agent-teams)).
   - This is exactly why the owner's rule "the tech lead plans and doesn't code" matters.
9. **Humans at checkpoints.** Agents should get "ground truth from the environment at each step", with "human feedback at checkpoints or when encountering blockers" ([Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)).

### 2.2 Failure modes to design against

| Failure mode | Evidence | Counter-measure in this plan |
|---|---|---|
| **Specs broken or unclear from the start** (system design) | MAST, 1,600+ traces across 7 frameworks: failures cluster into system design, inter-agent misalignment and **task verification** ([Cemri et al., "Why Do Multi-Agent LLM Systems Fail?"](https://arxiv.org/abs/2503.13657)) | Task card with acceptance criteria; the PM owns scope (5.2, 5.6) |
| **Agents rubber-stamping each other** | LLM judges favor output that is familiar to them (low perplexity), including their own model family's; stronger models can show more of it ([Self-Preference Bias in LLM-as-a-Judge](https://arxiv.org/abs/2410.21819), [rubric-based follow-up](https://arxiv.org/abs/2604.06996)) | A reviewer in a fresh context with read-only tools and a different model from the author where possible; evidence required; seeded "canary" defects to measure catch rate (5.3) |
| **Declaring victory early** | [Long-running harness post](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents); MAST task-verification category | The wave's feature list starts as "failing"; a `TaskCompleted` hook runs the DoD script |
| **Gaming tests**: hard-coding outputs, special cases for tests, loose tests, mocks in place of real code | Named in Claude system cards and reward-hacking benchmarks ([summary](https://arxiv.org/pdf/2511.21654), [Anthropic on reward hacking](https://www.anthropic.com/research/emergent-misalignment-reward-hacking)) | QA writes the acceptance tests from the spec **before** the build and keeps some hidden from the implementer; reviewers check the diff for test weakening |
| **Drifting from the spec, or scope creep** | MAST "disobey task specification"; guidance on clear task boundaries | Owned paths enforced by a hook; out-of-scope list on each card; the reviewer checks "nothing outside the task's scope changed" ([Best practices](https://code.claude.com/docs/en/best-practices)) |
| **File collisions between parallel agents** | "Two teammates editing the same file leads to overwrites" ([Agent teams](https://code.claude.com/docs/en/agent-teams)); InvAI's own drizzle-journal collisions | One owner per path per wave, enforced by a PreToolUse hook |
| **Lost memory between sessions** | Structured note-taking ([context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)) | ADRs, lessons file, `memory: project` for each role |
| **Too many findings leading to over-engineering** | "Chasing every finding leads to over-engineering" ([Best practices](https://code.claude.com/docs/en/best-practices)) | Findings are either blocking (correctness, requirements, security) or optional; at most 2 review rounds |

### 2.3 How the owner's proposed rules score

| Owner rule | Verdict | What to add so it holds |
|---|---|---|
| The tech lead plans and doesn't code | **Strongly supported** (the lead-starts-implementing failure) | Take away the tech lead's `Edit`/`Write` on source repos. Allow them only under `invai-docs/` through a path hook. Today v1-plan items #19–22 are marked "Tech lead · Fixed", so the lead did code |
| Every task has an owner, owned files and a DoD | Supported | Make it a template and have a hook check it at `TaskCreated`. Enforce owned paths in PreToolUse |
| Nothing ships without passing tests plus review by a different agent | Supported, with a caveat | "Different agent" isn't enough: same model plus same context is still biased. Require a fresh context, read-only tools, an evidence-based verdict, and a different model for high-risk changes |
| Every architecture decision recorded | Supported ([Nygard ADRs](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions), [adr.github.io](https://adr.github.io/)) | Record product and ops decisions too, not only architecture. Use one numbered folder |
| Waves of at most 5 tasks, then review | Supported by the 3–5 teammate guidance | Keep "at most 5 tasks, at most 3–4 running at once". Review each task when it finishes, not only at the end of the wave |
| MVP scope owned by the PM, nothing outside it built | Supported | Needs a written scope file and a change-request path. Otherwise "nothing outside it" blocks urgent fixes. Bugs, security fixes and incident fixes are always in scope |
| All tables tenant-scoped | Already enforced by the RLS coverage test | Add composite `(company_id, id)` foreign keys (open finding S-26), and state the exceptions: Better Auth tables, global reference data such as the trademark marks table |
| Idempotency for webhooks and payments | Supported ([Stripe on idempotency](https://stripe.com/blog/idempotency), [brandur.org](https://brandur.org/idempotency-keys)) | Widen it to **every** retried side effect: label purchase, tracking push, PO submit, scans. Open backlog item #8 (QC and bin calls have no idempotency key) shows the gap |
| Heavy work on the job queue | Supported | Define "heavy": more than 1 s at p95, any outside API call, any imaging call, any fan-out. Every job needs a jobId and a retry policy |

**Rules the owner didn't list but should add:**
1. **Evidence over assertion.** Every report shows the commands run and their output, or screenshots.
2. **Enforce rules with tools and hooks, not only prose.**
3. **Humans hold four gates:** production deploys, outbound communication, legal and marketplace submissions, and spending.
4. **Never weaken a test or a security control to get green.**
5. **Each wave ends with a lessons entry.**
6. **One scale test profile** (small, mid and large shop) in the definition of done for anything on the order path. The platform serves "all scales of users", and the seed today is one 300-order shop.

---

## 3. Gap analysis of the current 16 roles

### 3.1 Problems across the whole team

1. **No enforcement.**
   - No role file sets `tools`, `disallowedTools`, `permissionMode`, `skills`, `memory` or `maxTurns`.
   - `.claude/skills/` doesn't exist, and no hooks are configured (`.claude/settings.local.json` holds only three `gh` permissions).
   - So "Two agents never own the same file at the same time" (tech-lead) and "never use `withSystem` in a request path" (backend-foundation) rest on the model remembering them.
2. **Verifiers fix their own findings, and builders review their own work.**
   - `qa-engineer`: "you prove they work together … and you fix what doesn't, wherever it lives".
   - `security-reviewer`: "You find problems, prove them, and fix them with tests". `security/v1-review.md` shows the reviewer took over five B1 and B2 fixes ("Security (took over from B1)"), and nobody independent reviewed those fixes.
   - `product-designer`: "Fix, don't just report. Implement the top fixes in `invai-web`, `invai-floor` or `invai-ui` yourself". The designer grades its own changes and edits files owned by the web, floor and design-system engineers.
   - `pilot-success`: "you may make [fixes] in `invai-backend`", which crosses the owned-path boundary.
3. **The handbook's push rule skips review.** CLAUDE.md says "once the work is done and the definition of done passes, push straight to `main`", and "an agent working alone pushes its own finished work". The DoD in CLAUDE.md has no review step, which conflicts with the owner's rule.
4. **Ownership contradictions.**
   - `architect` says "You own `invai-contracts`".
   - S-27 in the security review says "A dedicated accept/decline procedure needs a contract change (QA owns contracts)".
   - The v1-plan backlog assigns contract items to QA (#15 "QA (contract + floor)").
5. **Stale and contradictory facts copied into prompts.**
   - v1-plan section 7 says "Not pushed: every repo's work is on local branch `platform-v1`", while CLAUDE.md says all work is on `main`.
   - S-19 says "sign-in 10/min", while backlog #20 and the role files say 20/min.
   - Role files repeat long as-built descriptions (DataTable APIs, endpoints, known gaps) that will drift. They belong in READMEs or skills ([Best practices](https://code.claude.com/docs/en/best-practices): don't put in CLAUDE.md "anything Claude can figure out by reading code").
6. **Role files point to folders that don't exist**: `invai-docs/specs/`, `invai-docs/pilots/`, `invai-docs/design/`. There is no `decisions/`, no `scope.md` and no lessons file. The only decision record is a table plus "Decision:" paragraphs inside v1-plan section 6.
7. **No live-service ownership.**
   - No role owns logs, error tracking, alerting, SLOs, the incident process or on-call.
   - The code has no Sentry, OpenTelemetry or PostHog, although `tools-stack.md` plans "Sentry + PostHog + Axiom".
   - The SP-API readiness list in `security/v1-review.md` requires "an incident-response plan (Amazon must be notified within 24 h)". [Amazon's DPP](https://developer-docs.amazon/sp-api/docs/protecting-amazon-sp-api-applications-incident-response) also requires critical vulnerabilities fixed within 7 days and high ones within 30. Someone has to own those clocks.
8. **Built for one shop size.**
   - The PM file fixes the customer at "US shops making 100–1,000 orders/day, 5–30 staff".
   - The owner wants all scales. Research 02 notes that small shops sit on "$49–149/mo" tools and that incumbents lose on "slow onboarding".
   - Nobody owns self-serve onboarding for a one-person shop, or performance for a 3,000-orders-a-day shop.
9. **No one owns go-to-market.**
   - No site, pricing page, comparison pages, Shopify App Store listing, lifecycle email, help center or support process.
   - "Draft messages … for the human founder to send" appears in three roles, and nobody owns the queue of drafts.

### 3.2 Role by role

| Role | Keep? | Specific weak spots (quoted) | Fix |
|---|---|---|---|
| **tech-lead** | Keep, narrowed to planning only | "accountable for the whole product working, **not for writing most of the code**" allows some coding (the owner wants none). "How you review: Read every report critically. Check claims that matter yourself" makes the planner the reviewer too, which doesn't scale and isn't independent. "Log every decision … in v1-plan section 6" keeps a single file that keeps growing. Model guidance names Fable/Opus/Sonnet but not which model **reviews** which | Tools: Read, Grep, Glob, Bash (read-only), plus Edit/Write limited to `invai-docs/waves/**`, `decisions/**` and `team/**`. Tasks come only from PM-approved scope. Review goes to the reviewer role; the tech lead integrates and runs the final gate |
| **architect** | Keep | Good rules ("Additive by default", "Record the reason … in a doc comment"). But decisions live only in code comments, with no ADR. "Known open contract items" will go stale. No versioning or deprecation policy for a public API, which the vendor portal and future partners will need | Owns ADRs for cross-cutting design; adds a deprecation policy; reviews every backend task for contract fit |
| **backend-foundation** | Keep | Solid. "Open items: S-15 … S-26" duplicates the security log. No zero-downtime migration rule: "Never hand-edit an applied migration" covers history but not expand/contract for a live database. The seed is one shop ("about 25 s"), so there is no large-tenant seed | Adds the `zero-downtime-migration` and `add-tenant-table` playbooks and a `seed:scale` profile |
| **backend-engineer** | Keep (one or more instances, one module area each) | v1-plan has "Backend engineers ×3" (B1/B2/B3) but one generic file, so the module area has to come from the task card. It owns `src/ai/` by default ("Invoke the `claude-api` skill before touching Anthropic SDK code"), but nothing covers evals, prompt regression or AI cost per tenant. "Add a migration only if the existing tables really can't hold it" is good | Module area comes from the task card; `src/ai/**` moves to the new ai-engineer |
| **integrations-engineer** | Keep | Very good ("Official docs first", "Verify, then enqueue", "The mock stays"). Missing: sandbox credentials and app approvals depend on the human; approval packets and marketplace review requirements such as Shopify's three GDPR webhooks ([Shopify privacy compliance](https://shopify.dev/docs/apps/build/compliance/privacy-law-compliance)) are listed as facts but have no owner; there is no rule for version upgrades or deprecation alerts | Application packets and policy watch move to compliance; adds a `provider-deprecation-watch` step |
| **imaging-engineer** | Keep | Excellent domain rules ("Physical size is sacred", "Measure peak RSS"). Gaps: no performance budget for peak-day volume (many sheets at once, queue concurrency), and the ICC-profile gap is noted without an owner | Adds the perf budget to its DoD; the QA scale test covers throughput |
| **web-engineer** | Keep | Good UX rules. Doesn't cover analytics events, performance budgets (only floor mentions bundle size) or self-serve onboarding and billing screens. "add it to invai-ui through the design-system engineer, or build it locally and report it" invites drift | Implements the event taxonomy from data-analyst; owns onboarding and billing UI screens |
| **floor-engineer** | Keep | Best role file ("A mismatch must block"). Known gaps listed but no owner decision (for example "The JS bundle is about 818 kB") | No change beyond the shared templates |
| **design-system-engineer** | **Merge into product-designer** | 35 lines. The work is small, well trodden and on the same surface the designer already edits ("add it to `invai-ui` with the design-system conventions"). Two roles on one repo produce the ownership overlap in 3.1 #2 | product-designer owns `invai-ui` and `invai-docs/design/**`; web and floor engineers implement screens |
| **product-designer** | Keep, redefined | "Fix, don't just report … in `invai-web`, `invai-floor` or `invai-ui` yourself" breaks single ownership and self-review. No research role: it designs "for people under time pressure" but can't reach them. No UX-copy ownership | Owns the UI kit, UX specs and UX copy (en/es); files UX tasks for web and floor; reviews every UI task |
| **devops-engineer** | **Rename to platform-sre and widen** | "Developers need one command … and production needs infrastructure that passes Amazon's data-protection review" says nothing about running production. Its open items list "central logging and alerts" and "backup restore drills" with no process around them | Adds observability, SLOs, incident response, restore drills, cost reports and release mechanics |
| **qa-engineer** | Keep, as verifier only | "fix what doesn't, wherever it lives" makes QA the unreviewed fixer of the whole codebase. Suites cover one seed shop only. No test-first role | Writes acceptance tests from the spec before the build; bugs go to the owner (it may fix only test code and fixtures); adds the scale suite |
| **security-reviewer** | Keep, as reviewer (fixes by owners) | "find problems, prove them, and fix them with tests" plus taking over B1/B2 fixes means nobody independent reviewed the security fixes. It owns both the findings log and the SP-API readiness list, which is compliance work | Writes the failing test and the finding; the owner fixes; security verifies. Exception: a live High incident. SP-API packet moves to compliance |
| **tech-writer** | **Rename to docs-writer and widen** | Docs for developers and the demo only. "Release notes / changelog | … Merged work only" is the only customer-facing output. No help center, no in-app help, no Spanish shop docs beyond floor instructions | Adds the help center (en/es), in-app help text, release notes, and support macros with customer-success |
| **product-manager** | Keep | "Customer: US shops making 100–1,000 orders/day" is too narrow for all scales. The pricing hypothesis ($149 / $349 / $699) conflicts with research 02's "$49–149/mo … undercutting Pythias" for small shops, with no experiment owner. "Before each build wave: a ranked list of at most 5 items" is good. No scope file | Owns `invai-docs/product/scope.md` and the segment definitions (small, mid, large); runs pricing experiments with data-analyst |
| **pilot-success** | **Rename to customer-success and widen** | "The first 2–3 pilot shops" becomes stale the day shop #4 signs up. No support process: tickets, severity, SLAs, macros. "may make [fixes] in `invai-backend`" crosses ownership | Onboarding at three service levels (self-serve, assisted, white-glove), support triage, churn review; fixes go through task cards |

### 3.3 Candidate new roles, tested against "distinct ongoing work and distinct files"

| Candidate | Distinct ongoing work | Distinct files and outputs | Decision |
|---|---|---|---|
| Independent reviewer | Every task needs a fresh-context review (the owner's rule) | `invai-docs/waves/<n>/reviews/*.md`; read-only | **Add** |
| AI engineer | Prompts, model routing, evals, cost and refusal handling for listings, trademark, personalization checks and the assistant, the product's AI edge | `invai-backend/src/ai/**`, `invai-backend/evals/**` | **Add** |
| SRE / observability | Logs, alerts, SLOs, incidents, restores | `invai-infra/**`, dashboards, `invai-docs/ops/**` | Merge into **platform-sre** (same files as devops) |
| Data / analytics | Metric definitions, pilot KPIs, event taxonomy, unit economics, experiment readouts, weekly metrics | `invai-docs/metrics/**`, `invai-backend/scripts/analytics/**`, dashboard definitions | **Add**; starts at pilot go-live |
| Marketplace and privacy compliance | Approvals for 5 marketplaces, the DPP packet, GDPR and DSAR process, policy watch (Etsy Creativity Standards, late-dispatch rules), ToS and privacy drafts | `invai-docs/compliance/**`, `invai-docs/legal/**` (drafts) | **Add** (phase 0 in the concept is "Paperwork", which is happening now) |
| Growth / marketing | Website, positioning, SEO comparison pages vs Pythias, MyDesigns and ShipStation, Shopify App Store listing, lifecycle email, launch | New `invai-site` repo, `invai-docs/growth/**` | **Add**; starts before public launch |
| Support (separate) | Ticket triage, macros | Same outputs as customer-success | Merge into **customer-success** (early-stage roles blur) |
| Finance / pricing | Plans, per-label margin, AI and infra cost | Models in `invai-docs/metrics/` | **No new role**: the PM decides, data-analyst models, platform-sre reports cost, the owner decides money |
| Legal | Terms, privacy, DPA | Drafts only | **No new role**: compliance drafts, and a human lawyer reviews |
| Sales | Demos, objection handling | Demo guide, battlecards | **No new role**: founder-led sales ([Activated Scale](https://www.activatedscale.com/feeds/blog/first-sales-hire-b2b-saas)); growth writes battlecards, docs-writer keeps the demo guide |

---

## 4. Final roster (20 roles)

Model guidance: **Fable** for keystone and cross-repo reasoning, **Opus** for building and review, **Sonnet** for config, docs and well-trodden UI. For high-risk changes, the reviewer should use a different model from the author (self-preference bias, 2.2).

"Starts" says when the role is used. Roles marked **Trigger** stay out of rotation until then, and no more than 3–5 agents run at once.

### Plan and decide

**1. tech-lead** (Opus, now). The team's planner and integrator, and never an implementer.
- Turns the PM's ranked scope into waves of at most 5 task cards, with one owner, one reviewer, owned paths, dependencies and interfaces agreed up front.
- Runs the wave gates, integrates results, runs the final verification on a fresh seed, and writes the owner report.
- Tools are read-only for code. It can write only under `invai-docs/waves/`, `decisions/` and `team/`.
- It may not create a task outside `scope.md`. It escalates trade-offs to the owner with a recommendation.

**2. product-manager** (Opus, now). Owns *what* and *why*.
- Maintains `invai-docs/product/scope.md` (MVP in and out, segments: small, mid, large), the ranked backlog, specs with Given/When/Then criteria, and the pricing hypothesis.
- Approves or rejects scope-change requests and reviews each wave plan against scope.
- Runs pricing and packaging experiments with data-analyst.
- Drafts customer and partner messages for the owner to send.

**3. product-designer** (Opus; absorbs the design-system engineer, now). Owns `invai-ui` and `invai-docs/design/**`: the component library, tokens, accessibility, UX specs for new screens (states, edge cases, three viewport sizes), and UX copy in English and Spanish.
- Audits running flows with screenshots and turns findings into task cards for web and floor.
- Doesn't edit `invai-web` or `invai-floor`.
- Reviews every UI task for UX and copy.

### Build

**4. architect** (Fable, now). Owns `invai-contracts` and the ADR practice.
- Additive-by-default contract changes, a deprecation policy for public and partner APIs, state machines, the permission model.
- Writes or approves every ADR for a cross-cutting decision.
- Reviews every task that touches the contract or crosses modules.

**5. backend-foundation** (Fable, now). Owns the backend core:
- DB conventions, migrations tooling, RLS, auth and floor auth, outbox, queues, realtime, guard, state machine, crypto, seed (including a scale seed), and `src/test/**`.
- Keeps the module patterns README true.
- Owns the `zero-downtime-migration` and `add-tenant-table` playbooks and reviews any migration written by someone else.

**6. backend-engineer** (Opus, now; one or more instances, one module area per task card). Builds features inside `src/modules/<area>/**` using the foundation's patterns.
- Idempotent jobs, tenant-isolation tests, exercised with curl as the right role.
- Never touches another module's tables.

**7. integrations-engineer** (Opus, now). Owns `src/integrations/**` (except `ai`), `src/api/webhooks.ts` and adapter fixtures.
- Moves each marketplace, carrier and supplier adapter from mock to production against real sandboxes, following the docs-first, verify-then-enqueue and polling-backstop rules.
- Owns per-connection health reporting.
- Watches provider versions and deprecations.

**8. ai-engineer** (Opus, new, now). Owns `src/ai/**` and `evals/**`: prompts, the model config, routing and effort, structured output validators, PII scrubbing at the gateway, refusal and fallback handling, and cost per tenant.
- Keeps an eval set per AI feature (listing drafts per channel limits, trademark-risk recall on known marks, personalization-flag accuracy, assistant answers against the seed ledger).
- No model or prompt change ships without an eval diff.
- Separate from backend-engineer because the work is ongoing (new models, prompt regressions) and the files are distinct.

**9. imaging-engineer** (Opus, now). Owns `invai-imaging`: nesting, compose, PDF, QA, personalization render, mockups.
- Physical-size and QR-scannability tests, peak-RSS and throughput budgets recorded in the README.

**10. web-engineer** (Opus, now). Owns `invai-web`: dashboard, vendor portal, self-serve onboarding, billing screens, analytics events (to data-analyst's taxonomy).
- Every screen has loading, empty, error and partial states, works in English and Spanish and in light and dark, and Today and Orders work at 390 px.

**11. floor-engineer** (Opus, now). Owns `invai-floor`.
- Scan correctness, idempotent offline outbox, glove-sized UI, English and Spanish.
- The rule that a mismatch must block is non-negotiable.

### Verify

**12. reviewer** (Opus or Fable, the opposite of the author's model for high-risk changes; new, now). Independent, fresh-context, **read-only** review of every task (tools: Read, Grep, Glob, Bash; no Edit or Write).
- Checks the diff against the task card: acceptance criteria met, tests really exercise the behavior (no special cases, no weakened assertions), nothing outside owned paths or scope changed, conventions (tenancy, idempotency, i18n, money in cents), and it re-runs the verification commands itself.
- The verdict is `approve`, `changes-required` (blocking findings only) or `escalate`. Output goes to `invai-docs/waves/<n>/reviews/`.

**13. qa-engineer** (Fable, now). Owns the E2E suites, the scale test profile (small, mid, large shop seeds), release verification and `qa-report.md`.
- Writes acceptance tests from the spec **before** implementation, some held back from the implementer.
- Root-causes cross-repo failures and files them to the owning role.
- Edits only test code, fixtures and the QA report.

**14. security-reviewer** (Opus, now). Owns threat models, `security/v1-review.md`, the RLS and permission-matrix test suites, dependency audits and SP-API security controls.
- Proves each issue with a failing test, then hands the fix to the owner and verifies it.
- May fix directly only during a declared High incident, and that fix still gets a reviewer.
- Mandatory co-reviewer on any task flagged auth, PII, tenancy, webhooks, files or payments.

### Run

**15. platform-sre** (Sonnet for config, Opus for incidents; renamed from devops, now). Owns `invai-infra`, CI and CD, environments, observability (errors, logs, traces, uptime, alert rules), SLOs (API availability, sync freshness, label-purchase success), incident response and postmortems, backup-restore drills, release mechanics and cloud cost reports.
- Never deploys to a real environment without the owner's go-ahead.
- Owns the 7-day and 30-day vulnerability-fix clocks with security.

### Customers and market

**16. customer-success** (Opus; renamed from pilot-success, now). Owns onboarding at three service levels:
- self-serve for small shops,
- assisted for mid-size shops,
- white-glove for large and multi-location shops.

It also owns pilot profiles and dry-run imports, the issue log, support triage (severity, reproduction, owner), macros, churn-risk reviews and the weekly customer update.
- Keeps real PII off the repos.
- Never contacts customers directly; drafts go to the owner inbox.

**17. docs-writer** (Sonnet; renamed from tech-writer, now). Owns developer docs (READMEs, runbook, architecture-as-built), the demo guide, the help center and in-app help in English and Spanish, and release notes.
- Everything is verified against the running code; when code and docs disagree, the code wins.
- Reviews user-facing copy for plain language.

**18. compliance-officer** (Opus; new, now, because phase 0 is paperwork). Owns `invai-docs/compliance/**` and `invai-docs/legal/**`:
- marketplace application packets (Etsy commercial access, Amazon SP-API with the DPP evidence pack, Shopify App Store including GDPR webhooks, TikTok Partner, Walmart Solution Provider),
- the privacy request (DSAR) process,
- AI-disclosure and Creativity Standards checks for listings,
- policy-change watch,
- first drafts of ToS, the privacy policy and the DPA for a lawyer,
- security questionnaires.

The human submits and signs everything.

**19. data-analyst** (Opus; new, **Trigger: first pilot goes live**). Owns metric definitions (`invai-docs/metrics/`), the analytics event taxonomy, pilot KPI computation (late rate, film use, reprint rate, minutes saved), unit economics (per-label margin, AI and infra cost per tenant, plan fit by segment), experiment readouts and the weekly metrics review.
- Read-only on production data through approved views; never sees raw PII.

**20. growth-marketer** (Sonnet for drafts, Opus for strategy; new, **Trigger: four weeks before public launch or the app-store listing**). Owns `invai-site` (landing, pricing, comparison pages), positioning and battlecards, SEO, marketplace app-store listing copy, lifecycle and onboarding email sequences, and launch plans.
- Every claim needs evidence (no fake reviews or unverified numbers).
- Nothing is published or sent without the owner.

**Roles that stay with the human owner:**
- sales conversations, customer replies,
- signing and submitting,
- production deploy go-ahead, spending, pricing,
- lawyer review, the 24-hour Amazon incident notice,
- final scope calls.

---

## 5. Skill matrix: reusable playbooks

Each playbook is a `.claude/skills/<name>/SKILL.md` of 500 lines or fewer, with a precise `description` ([Skills](https://code.claude.com/docs/en/skills)). Details on how to set them up:
- Preload the playbooks each role needs with the subagent's `skills:` field. Note that `skills` is **not** applied to agent-team teammates, which load project skills themselves ([Agent teams](https://code.claude.com/docs/en/agent-teams)).
- Set `disable-model-invocation: true` on playbooks with outside side effects, so only the human triggers them: `deploy-to-environment`, `send-owner-draft`.
- Use `` !`command` `` injection to ground a playbook in live state, such as `git diff` or the current wave file.
- Move the long "how it works (as built)" sections out of the role files and into playbooks or READMEs, so each role file stays near 40 lines.

### 5.1 Shared by every role

| Playbook | What it makes the agent do |
|---|---|
| `task-intake` | Read the task card, confirm owned and read-only paths, restate acceptance criteria, list unknowns before coding |
| `verify-and-report` | Run the DoD commands, exercise the feature for real, and write the evidence report (commands, output, screenshots, decisions, known gaps) |
| `record-decision` | Write an ADR (Nygard format: context, decision, status, consequences) and link it from the wave file |
| `log-lesson` | Add a lessons entry (what happened, cause, rule change, where it's now enforced) |
| `escalate-to-owner` | Add a one-page decision request to the owner inbox (question, options, recommendation, deadline, default if silent) |
| `write-plain-language-copy` | Shop words, short sentences, what happened plus what to do next, real Spanish |
| `scrub-pii-fixture` | Turn real data into a fixture: fake names, emails, phones and addresses; keep structure, SKUs and personalization shapes |
| `respect-ownership` | What to do when blocked by someone else's file: work around it locally, report it, never edit it |
| `read-before-change` | Check library APIs in `node_modules` or official docs (the newer-than-training libraries list) |

### 5.2 Engineering playbooks

| Playbook | Primary role | Also used by |
|---|---|---|
| `add-contract-procedure` | architect | backend-engineer, web, floor (consumer checklist) |
| `contract-deprecation` | architect | integrations |
| `add-tenant-table` (company_id, RLS policy, composite FK, indexes, coverage test) | backend-foundation | backend-engineer, ai-engineer, reviewer |
| `zero-downtime-migration` (expand, backfill in a job, switch, contract; never lock a hot table) | backend-foundation | backend-engineer, platform-sre, reviewer |
| `idempotent-job` (jobId key, safe retry, replay test) | backend-foundation | backend-engineer, integrations, ai-engineer |
| `idempotent-side-effect` (webhooks, payments, label buys, tracking push, scans: key, stored first result, conflict on changed params, per [Stripe](https://stripe.com/blog/idempotency)) | backend-foundation | integrations, floor, reviewer, security |
| `add-backend-feature` (router, service, jobs, events, tests, curl as the role) | backend-engineer | — |
| `add-marketplace-integration` (docs-first, endpoints and scopes list, fixtures, contract tests, sandbox run, verify-then-enqueue, polling cursor, token refresh, rate limiter, health, runbook row) | integrations | compliance (approval side), security |
| `add-carrier-or-supplier-adapter` | integrations | — |
| `provider-deprecation-watch` | integrations | compliance |
| `ai-feature-with-evals` (prompt, schema validator, eval set, model and effort choice, PII scrub, cost per call, mock provider) | ai-engineer | backend-engineer |
| `model-upgrade` (run evals old vs new, cost diff, rollout) | ai-engineer | data-analyst |
| `imaging-change-with-budget` (dimension tests, QR decode, peak RSS, throughput) | imaging | qa |
| `build-dashboard-screen` (states, i18n, 390 px, light and dark, screenshots) | web | product-designer |
| `build-floor-flow` (block on mismatch, idempotent scan, 64 px targets, sound, keyboard-only, offline) | floor | product-designer |
| `add-ui-component` (Radix or Base UI, tokens, a11y, playground, en/es) | product-designer | web, floor |
| `instrument-analytics-event` (from the taxonomy, no PII, tenant-tagged) | web | data-analyst, backend-engineer |
| `root-cause-bug` (reproduce, find the faulty layer, lowest-layer regression test) | qa | all engineers |
| `scale-test` (small, mid and large seed profiles; p95 targets for order list, import, sheet build, label batch) | qa | backend-foundation, imaging, platform-sre |

### 5.3 Review and quality playbooks

| Playbook | Primary role | Also used by |
|---|---|---|
| `independent-review` (diff vs card, re-run checks, test-weakening scan, scope check, blocking vs optional) | reviewer | architect, security, product-designer as co-reviewers |
| `acceptance-tests-first` (from the spec, some held back) | qa | product-manager (criteria) |
| `run-golden-path` (clean start, fresh seed, API, browser and floor suites) | qa | tech-lead (final gate), platform-sre (release) |
| `threat-model-change` | security | architect, integrations, ai-engineer |
| `tenant-isolation-audit` | security | reviewer |
| `dependency-and-container-audit` | security | platform-sre |
| `release-checklist` (all suites, migrations reviewed, rollback plan, release notes, owner go-ahead) | platform-sre | tech-lead, docs-writer |

### 5.4 Operations playbooks

| Playbook | Primary role | Also used by |
|---|---|---|
| `deploy-to-environment` (manual trigger only) | platform-sre | — |
| `add-observability` (structured logs with PII redaction, error tracking, trace ids across API, worker and imaging, alert rule plus runbook link) | platform-sre | backend-foundation, integrations |
| `define-slo` (for example sync freshness under 15 min, label purchase success, API availability) | platform-sre | product-manager |
| `incident-response` (severity, incident commander, comms drafts, evidence preservation, Amazon 24 h notice path, status updates) | platform-sre | security, customer-success, compliance |
| `postmortem` (blameless: contributing causes, not people, per [Google SRE](https://sre.google/sre-book/postmortem-culture/)) | platform-sre | all, feeding `log-lesson` |
| `backup-restore-drill` | platform-sre | backend-foundation |
| `cost-review` (cloud, AI tokens per tenant, label fees) | platform-sre | data-analyst, ai-engineer |

### 5.5 Product, customer and market playbooks

| Playbook | Primary role | Also used by |
|---|---|---|
| `write-spec` (problem and evidence, users, in/out, flow, Given/When/Then, metrics, open questions) | product-manager | product-designer |
| `prioritize-backlog` (impact on the top pains × shops affected × effort × risk × outside-approval dependency) | product-manager | tech-lead |
| `scope-change-request` | product-manager | anyone may file one |
| `pricing-experiment` (hypothesis, segment, offer, success metric, readout) | product-manager | data-analyst, growth |
| `competitive-watch` (Pythias, MyDesigns, Fulfill Engine, ShipStation pricing and feature moves) | product-manager | growth |
| `ux-audit` (screenshots at 1440, 390 and 1280×800; ranked findings) | product-designer | customer-success (real-user evidence) |
| `usability-test-plan` (script for the owner to run with a presser or office user) | product-designer | customer-success |
| `onboard-shop` (tiered: self-serve checklist, assisted call pack, white-glove data migration) | customer-success | docs-writer |
| `import-dry-run` (parse rate, SKU auto-map rate, ship-by accuracy, personalization read) | customer-success | integrations, qa |
| `triage-support-ticket` (severity: blocks shipping > wrong print > staff time > annoyance; reproduce; owner; workaround; macro) | customer-success | qa, docs-writer |
| `churn-risk-review` | customer-success | data-analyst |
| `write-help-article` (en/es, symptom-first, screenshots from the running app) | docs-writer | customer-success |
| `release-notes` | docs-writer | growth |
| `define-metric` (name, formula, SQL, owner, segment cuts) | data-analyst | product-manager |
| `weekly-metrics-review` | data-analyst | product-manager, customer-success |
| `experiment-readout` | data-analyst | product-manager, growth |
| `unit-economics-model` | data-analyst | product-manager, platform-sre |
| `marketplace-app-application` (a per-marketplace packet: requirements, evidence, screenshots, data-flow diagram, reviewer notes) | compliance | integrations, security |
| `amazon-dpp-evidence-pack` | compliance | security, platform-sre |
| `privacy-request-handling` (Shopify `customers/data_request`, `customers/redact`, `shop/redact`; DSAR clock) | compliance | integrations, backend-engineer |
| `policy-change-watch` (Etsy Creativity Standards, AI disclosure, dispatch SLAs, USPS rule changes) | compliance | product-manager, integrations |
| `listing-compliance-check` (AI disclosure, production partner, trademark-risk threshold) | compliance | ai-engineer |
| `legal-doc-draft` (ToS, privacy policy, DPA, subprocessor list, marked "draft for counsel") | compliance | — |
| `security-questionnaire` | compliance | security |
| `landing-page` | growth | product-designer, docs-writer |
| `seo-comparison-page` (InvAI vs Pythias, MyDesigns and ShipStation, with sourced, dated claims) | growth | product-manager |
| `lifecycle-email-sequence` (trial onboarding, activation nudges, win-back) | growth | customer-success |
| `app-store-listing` (Shopify App Store, and later Etsy app gallery text) | growth | compliance |
| `launch-plan` | growth | product-manager, customer-success |
| `send-owner-draft` (any outbound message is queued, never sent) | all customer-facing roles | — |

### 5.6 Matrix at a glance

Legend:
- **P**: primary owner of the playbook.
- **U**: the role uses the playbook regularly.
- **R**: the role reviews work that uses it.

The nine shared playbooks (5.1) apply to every role and aren't repeated here.

| Playbook group | TL | PM | Des | Arch | BF | BE | Int | AI | Img | Web | Flr | Rev | QA | Sec | SRE | CS | Docs | Comp | Data | Grow |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Contract / ADR | U | | | P | U | U | U | U | | U | U | R | | R | | | | | | |
| Schema, migration, tenancy | | | | R | P | U | U | U | | | | R | | R | U | | | | | |
| Idempotency, jobs | | | | R | P | U | U | U | | | U | R | | R | | | | | | |
| Integrations | | | | R | | | P | | | | | R | U | R | | U | | U | | |
| AI and evals | | | | | | U | | P | | | | R | | R | | | | U | U | |
| Imaging | | | | | | | | | P | | | R | U | | | | | | | |
| UI and screens | | R | P | | | | | | | P | P | R | U | | | | | | | |
| Review and verification | U | | R | R | R | | | | | | | P | P | P | U | | | | | |
| Ops, incidents | | | | | U | | U | | | | | | | U | P | U | | U | | |
| Specs, scope, pricing | R | P | U | | | | | | | | | | U | | | U | | | U | U |
| Customer, support, help | | U | U | | | | U | | | | | | U | | | P | P | | U | U |
| Compliance and legal | | U | | | | | U | U | | | | | | U | U | | | P | | U |
| Metrics, experiments | | U | | | | | | U | | U | | | | | U | U | | | P | U |
| Growth | | U | U | | | | | | | | | | | | | U | U | R | U | P |

---

## 6. Team operating system

### 6.1 Wave cadence

A wave has **at most 5 task cards, with 3–4 agents running at once**. It moves through these steps:

1. **Scope (PM).**
   - Pick up to 5 items from `scope.md` and the backlog, each with a spec.
   - Bugs, security findings and incidents skip the queue, but still get a card.
2. **Plan (tech lead).**
   - Write the wave file `invai-docs/waves/<n>/wave.md` and the cards (6.2).
   - Record the agreed cross-module function names, and have providers commit stubs first.
   - The **PM reviews the plan** against scope, and the **architect** reviews it for cross-cutting design. The tech lead doesn't approve its own plan.
3. **Acceptance tests first (QA).** For each card, write the acceptance tests. Some stay visible, some are held back from the implementer.
4. **Build (owners).**
   - Each owner works only in its owned paths and ends with `verify-and-report`.
   - A `TaskCompleted` hook runs the card's DoD commands and blocks completion on failure.
5. **Review, per task, as each finishes** (6.3). There are at most 2 rounds; then the tech lead escalates.
6. **Integrate (tech lead plus QA).**
   - Fresh reset, migrate and seed, then all E2E suites plus the scale profile.
   - The tech lead looks at the key screens and commits and pushes after the gate. The owner pushes only when working alone **and** the review passed.
7. **Retro (tech lead).**
   - 15 minutes' worth of text: what slipped, reviewer catch rate, lessons.
   - Update `lessons.md` and promote any rule into a hook, skill or role file.
8. **Owner report.** What works, the evidence, what went wrong, and decisions needed, in plain language with no inflation.

### 6.2 Task card template (`invai-docs/waves/<n>/T-<n>-<slug>.md`)

```
id: T-12-03                     wave: 12
title: Idempotent QC pass and bin assign
spec: invai-docs/specs/qc-idempotency.md   scope ref: scope.md#floor-correctness
owner: backend-engineer (area: production)  reviewer: reviewer   co-reviewers: floor-engineer
risk flags: [idempotency, floor-correctness]   # tenancy | pii | auth | payments | webhooks | migration | marketplace-policy | ai
owned paths (edit):    invai-backend/src/modules/production/**
read-only paths:       invai-contracts/src/**, invai-floor/src/outbox/**
depends on: T-12-01 (contract: production.qc accepts clientScanId)
interfaces promised:   qcPass(tx, ctx, {itemId, clientScanId}) -> ScanResult
acceptance criteria:
  1. Given an item already packed by clientScanId X, when QC pass is replayed with X, then the result equals the first and no transition row is written.
  2. ... (edge cases: different clientScanId on a packed item -> INVALID_TRANSITION; cancelled item -> BLOCKED result)
verification: pnpm typecheck && pnpm lint && pnpm test; curl script scripts/verify/T-12-03.sh as presser; floor e2e press.spec
out of scope: bin relabeling UI, scanBatch
budget: maxTurns 150; escalate if blocked > 30 min of work
DoD: CLAUDE.md DoD + tests for replay + no NOT_IMPLEMENTED in production.* + report
```

A `TaskCreated` hook rejects a card that is missing an owner, reviewer, owned paths, acceptance criteria, verification commands or a scope ref. Four more hooks back the rules up:
- A **PreToolUse** hook blocks Edit/Write outside the card's owned paths.
- A second PreToolUse hook blocks `git push --force`, `sst deploy` and `db:reset` on the shared DB while agents are running.
- A **Stop** hook for implementers runs the verification script.

Sources: [Agent teams](https://code.claude.com/docs/en/agent-teams) and [Best practices](https://code.claude.com/docs/en/best-practices).

### 6.3 Review protocol: who reviews whom

| Author | Primary reviewer | Mandatory co-reviewer when |
|---|---|---|
| Any engineer (backend, integrations, AI, imaging, web, floor, foundation) | reviewer | architect: the contract changes or the task crosses modules. backend-foundation: a migration or new table. security: the task is flagged tenancy, PII, auth, webhooks, files or payments. product-designer: any UI. ai-engineer: prompts or models. qa: E2E or golden-path area |
| architect | reviewer (Fable ↔ Opus swap) | backend-foundation plus one consumer engineer |
| backend-foundation | reviewer (Opus) | security (auth, RLS, crypto) |
| product-designer (ui kit) | web-engineer or floor-engineer (as consumers) | reviewer for code quality |
| qa (test code) | the feature owner (does the test match intent?) | reviewer |
| security fix (incident exception) | reviewer | architect or backend-foundation |
| platform-sre (infra, CI) | security | the tech lead for release-affecting changes |
| tech-lead (wave plan) | product-manager (scope) | architect (design) |
| product-manager (spec) | product-designer (flow) and qa (testability) | customer-success (evidence) |
| docs-writer, growth, compliance, customer-success (documents) | one domain owner (for example integrations for an app packet) | compliance for any public claim or legal text |

**Rules to keep reviews honest:**
1. **Fresh context and read-only tools.** The reviewer gets the card, the diff and the report, and nothing about the author's reasoning.
2. **Evidence or it didn't happen.** A verdict must list the commands the reviewer re-ran and their results. A "LGTM" with no evidence counts as no review.
3. **Blocking findings only**: correctness, acceptance criteria, security, tenancy, idempotency, ownership and scope violations. Style notes are optional.
4. **Test-integrity scan.** Check for deleted or loosened assertions, `.skip`, broad mocks of the unit under test, special-case branches, and snapshot rewrites.
5. **Model diversity on high-risk flags.** Where possible the reviewer uses a different model from the author.
6. **Canary defects.** Once every few waves, the tech lead plants a known bug in a card's branch to measure reviewer catch rate, and records it in `lessons.md`. A rising "approve with no findings" rate with falling catch rates signals rubber-stamping.
7. **Two rounds at most, then escalate.** Disagreements between author and reviewer go to the tech lead. If they touch scope or risk, they go to the owner.

### 6.4 Escalation to the human owner

Agents escalate by writing to `invai-docs/owner-inbox.md`. Each entry has: an id, the question, 2–3 options, a recommendation, the cost of waiting, a deadline, and the default if there's no answer.

**Always escalate:**
- A production deploy, or anything that touches a real cloud account or real keys.
- Any outbound communication: shops, vendors, marketplaces, partners, public posts.
- Legal, marketplace or partner submissions and signatures.
- Spending, pricing changes, plan limits.
- Loading real shop data into any non-local environment.
- A High security finding or suspected PII incident: immediately, with the Amazon 24-hour clock stated.
- A scope change beyond MVP.
- Reopening a logged decision.
- Two failed review rounds.
- Any case where an agent would need to weaken a control or a test to proceed.

**Never escalate:** routine technical choices inside a card. Make the call and record it.

### 6.5 How decisions and scope are recorded

- **`invai-docs/decisions/NNNN-<slug>.md`**, one per decision, in Nygard format: context, decision, status (proposed, accepted, superseded by NNNN) and consequences ([Nygard](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions), [Fowler](https://www.martinfowler.com/bliki/ArchitectureDecisionRecord.html)).
  - Types: architecture (architect), product (PM), ops (SRE), security (security), process (tech lead).
  - Seed it by migrating v1-plan section 6's existing decisions: pack semantics, opt-in stock push, keep multi-repo, and the v1 cuts.
  - v1-plan section 6 then becomes an index plus the backlog table.
- **`invai-docs/product/scope.md`**, owned by the PM:
  - MVP in and out by segment (small, mid, large).
  - The "always in scope" classes: bugs, security, incidents, compliance deadlines.
  - A change log.
  - Changes come only through `scope-change-request`, approved by the PM. Changes that affect cost or risk also need the owner.
- **Backlog**: one table (id, item, owner role, status, link), owned by the tech lead, with the PM ranking it.
- **Fix the known contradictions first**:
  - Contracts are owned by the architect, not "QA owns contracts".
  - The `platform-v1` vs `main` note.
  - The sign-in limit (10/min vs 20/min).

### 6.6 How the team learns

1. **`invai-docs/team/lessons.md`** (append-only). Each entry records: date, wave or incident, what happened, the contributing cause (blameless, per [Google SRE](https://sre.google/sre-book/postmortem-culture/)), the new rule, and **where it's now enforced**.
2. **Promotion ladder for rules.** A rule starts as a lesson. On a second occurrence it moves into the relevant skill or role file. If it can be checked mechanically, it becomes a hook or a test. The goal is to move rules out of prose as often as possible.
3. **Prune CLAUDE.md every 3 waves.** Ask of each line: "Would removing this cause Claude to make mistakes?" ([Best practices](https://code.claude.com/docs/en/best-practices)). Move the as-built detail into READMEs.
4. **`memory: project` for each role**, stored in `.claude/agent-memory/<role>/` ([Subagents](https://code.claude.com/docs/en/sub-agents)). It holds codepaths, gotchas and provider quirks. The tech lead reviews these files in the retro, and anything useful to everyone moves to lessons or a skill.
5. **Team metrics, tracked in each wave file**:
   - first-pass review approval rate, and canary catch rate,
   - escaped defects (found by QA or a pilot after approval),
   - reopen rate,
   - cycle time per card, and tokens per card.

   Research ties performance mostly to token use and task design ([multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)), so watch cost per card as well as quality.
6. **Postmortem for every incident and every escaped High defect**, feeding lessons within 48 hours.

### 6.7 Suggested order to set this up (for the owner to approve)

1. Create `decisions/`, `product/scope.md`, `team/lessons.md`, `owner-inbox.md` and `waves/`, and fix the three contradictions.
2. Add `tools` limits to tech-lead, reviewer and security (read-only). Add the `TaskCreated`, `TaskCompleted` and PreToolUse (owned paths, dangerous commands) hooks.
3. Rewrite the role files:
   - Merge design-system into product-designer.
   - Rename devops, pilot-success and tech-writer.
   - Add reviewer, ai-engineer and compliance-officer now.
   - Keep data-analyst and growth-marketer as dormant files with their triggers.
4. Write the 9 shared playbooks, then the engineering and review ones, and add the rest as each role becomes active.
5. Run one pilot wave under the new rules (for example backlog #8 idempotent QC, S-15 email verification, S-28 verify-before-enqueue, observability baseline, Shopify GDPR webhooks). Measure the team metrics, and adjust.

---

## Sources

- Anthropic, [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- Anthropic, [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
- Anthropic, [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- Anthropic, [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- Anthropic, [Natural emergent misalignment from reward hacking](https://www.anthropic.com/research/emergent-misalignment-reward-hacking)
- Claude Code docs: [Best practices](https://code.claude.com/docs/en/best-practices), [Subagents](https://code.claude.com/docs/en/sub-agents), [Agent teams](https://code.claude.com/docs/en/agent-teams), [Skills](https://code.claude.com/docs/en/skills)
- Cemri et al., [Why Do Multi-Agent LLM Systems Fail? (MAST)](https://arxiv.org/abs/2503.13657)
- Wataoka et al., [Self-Preference Bias in LLM-as-a-Judge](https://arxiv.org/abs/2410.21819); [Self-Preference Bias in Rubric-Based Evaluation](https://arxiv.org/abs/2604.06996)
- [EvilGenie: A Reward Hacking Benchmark](https://arxiv.org/pdf/2511.21654)
- Nygard, [Documenting Architecture Decisions](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions); [adr.github.io](https://adr.github.io/); Fowler, [Architecture Decision Record](https://www.martinfowler.com/bliki/ArchitectureDecisionRecord.html)
- Google SRE, [Postmortem Culture](https://sre.google/sre-book/postmortem-culture/)
- Stripe, [Designing robust and predictable APIs with idempotency](https://stripe.com/blog/idempotency); [brandur.org idempotency keys](https://brandur.org/idempotency-keys)
- Amazon SP-API, [Incident response guidance](https://developer-docs.amazon/sp-api/docs/protecting-amazon-sp-api-applications-incident-response), [Data encryption](https://developer-docs.amazon/sp-api/docs/protecting-amazon-api-applications-data-encryption)
- Shopify, [Privacy law compliance (mandatory webhooks)](https://shopify.dev/docs/apps/build/compliance/privacy-law-compliance)
- Early-stage SaaS team sequencing: [Cerebral Ops](https://blog.cerebralops.in/first-10-hires-saas-startup-sequence/), [Activated Scale](https://www.activatedscale.com/feeds/blog/first-sales-hire-b2b-saas), [Seaport Search Partners](https://www.seaportsearchpartners.com/blog/hiring-your-first-customer-success-leader-what-founders-of-b2b-saas-startups-need-to-know)
- Internal: `invai/CLAUDE.md`, `.claude/agents/*.md`, `build/v1-plan.md`, `security/v1-review.md`, `00-platform-concept.md`, `research/02-competitors.md`, `research/03-pain-points.md`, `tools-stack.md`
