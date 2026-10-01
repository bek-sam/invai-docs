# T-P7-2: Shared `ConfidenceBadge` in `invai-ui` (B-134, kit half)

| Field | Value |
|---|---|
| Wave | P7 |
| Scope ref | `scope.md#market-signals` (shipped wave 18; B-134 is design-system debt on that screen) |
| Spec | backlog B-134; wave 18 T-18-5 designer co-review; the local component `invai-web/src/components/market/confidence-badge.tsx` (its header says why it is local) |
| Owner | product-designer |
| Reviewer | reviewer (opus) |
| Co-reviewers | none (the consumer review happens in T-P7-3) |
| Risk flags | ui (shared component) |
| Model | sonnet |
| Depends on | plan review (architect on the props) |

## Owned paths (edit)
- `invai-ui/src/app/confidence-badge.tsx` (new, architect R2), its test, `invai-ui/src/index.ts` (export line), `invai-ui/src/i18n/locales/**` if the kit carries the labels, `invai-ui/README.md` (one line in the component list if there is one)

## Read-only paths
- `invai-web/**`, `invai-contracts/**` (`ConfidenceBand` type), every other repo.

## Interfaces promised (T-P7-3 builds on these)
- Architect ruling R2: `export function ConfidenceBadge(props: ConfidenceBadgeProps)` and `export type ConfidenceBadgeProps = { band: ConfidenceBand; label?: string; className?: string }` from `@invai/ui`, with `import type { ConfidenceBand } from "@invai/contracts"` (the kit already depends on it, like `ChannelBadge`/`StatusBadge`) and exhaustive `Record<ConfidenceBand, …>` maps. Same look as the local web component: high → success + shield-check icon, medium → warning + flask icon, low → outline + circle-help icon; icon `aria-hidden`, text always shown (never color alone).
- Labels under `confidenceBand.*` in the kit's en/es locales: the kit's default English/Spanish text ("High confidence" / "Medium confidence: test it" / "Not enough data", and the Spanish the web catalog already uses for `market.band.*`), overridable with `label`.

## Acceptance criteria
1. `ConfidenceBadge` renders each band with its variant, icon and text; `label` overrides the text.
2. Spanish text matches `invai-web`'s current `market.band.*` Spanish exactly (copy it; no new wording).
3. A test covers the three bands and the override; a11y: the icon is hidden from screen readers, the text is the accessible name.
4. `pnpm typecheck && pnpm lint && pnpm test && pnpm build` pass in `invai-ui`.

## Verification
- `cd invai-ui && pnpm typecheck && pnpm lint && pnpm test 2>&1 | tail -n 20 && pnpm build 2>&1 | tail -n 10`.
- `grep -n "ConfidenceBadge" invai-ui/src/index.ts` shows the export.

## Out of scope
- Editing `invai-web` (T-P7-3), a vote-card component (B-134 mentions the pattern; only the badge is reused today, the digest has no badge), any other kit component.

## Rules
- Role file `.claude/agents/product-designer.md`; follow `add-ui-component` and `write-plain-language-copy`. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/product-designer/`.
- Other agents at the same time: qa-engineer (`invai-web/e2e/**`), platform-sre (`.claude/hooks/**`), ai-engineer (`invai-backend/src/ai/**`).
- Commit only your paths, attribution line at the end. **Don't push; only the tech lead pushes after the gate.** Foreground runs only; record any PID you start and list it (stopped) in the report.
- Trim output. Report (≤ 60 lines) to `invai-docs/waves/P7/reports/T-P7-2.md`, one line per milestone as you go.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
