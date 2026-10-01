# Review of T-P7-3 (round 1)

- Reviewer: product-designer on Claude Opus 5.5
- Author: web-engineer on Claude Opus 5.5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web show f20021b` | read in full |
| `invai-ui/src/app/confidence-badge.tsx` | read: `ConfidenceBadgeProps` is `{band, label?, className?}`; `label` overrides only the text, tone/icon always come from `band` |
| `invai-web/src/components/market/recommendation-card.tsx:2,52` (post-fix, line numbers approx.) | `<ConfidenceBadge band={...} />` — no `label`, no `className` override, no local tone/icon map re-added |
| `grep -n "dueño\|propietario" invai-web/src/i18n/es.ts` | "dueño" at lines 360, 947, 2505, 2506, 2526, 2628 (every other place the catalog names the account owner); "propietario" only at the new line 191 |
| `invai-backend/src/ai/breaker.ts:44-48`, `src/env.ts:86-87` | `spendCaps()` returns `{platform: env.AI_DAILY_PLATFORM_CAP_CENTS, tenant: env.AI_DAILY_TENANT_CAP_CENTS}` — both server env vars (defaults $500/day platform, $50/day tenant), not a per-company DB setting; `grep -rln "aiSpendCapCents\|spendCapCents"` across `invai-backend/src` finds no per-tenant override anywhere |
| :3000 | down, as the author reported; no browser exercise possible this round either |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | Kit `ConfidenceBadge` used with no local styling, no re-added local component |
| 2 | Yes | Kit's `confidenceBand.*` en/es is byte-identical to the dropped `market.band.*`; no visual change |
| 3 | Not re-run (primary reviewer already did) | — |
| 4 | Deferred to gate, per card | — |
| 5 | **Not fully met — copy is wrong, not just imperfect** | See blocking findings 1–2 |

## Blocking findings
1. `invai-web/src/i18n/en.ts` / `es.ts` — `assistant.error.spendCap`: "or ask the owner to raise it" / "o pídele al propietario que lo aumente" tells the user to do something that cannot work and isn't even their shop's problem alone. `invai-backend/src/ai/breaker.ts:44-48` shows the cap is `AI_DAILY_TENANT_CAP_CENTS` / `AI_DAILY_PLATFORM_CAP_CENTS`, two server env vars with no per-company override in the DB or in any settings screen — no shop owner has a control for this anywhere in the product. A platform-cap hit (same message, same code `spend_cap`) isn't "your shop's" limit at all; it's every tenant sharing one pool. Failure scenario: an office worker hits the cap, tells the owner "the AI says you can raise our limit," the owner opens Settings/Billing, finds nothing, and files a support ticket for a feature that doesn't exist — worse than saying nothing. Fix: drop the clause entirely; the only true, actionable instruction is to wait for the daily reset.
   - **EN** (`assistant.error.spendCap`): `"Your shop has reached today's AI limit. Try again tomorrow."`
   - **ES** (`assistant.error.spendCap`): `"Tu tienda alcanzó el límite diario de IA. Vuelve a intentarlo mañana."`
2. `invai-web/src/i18n/es.ts:191` — "propietario" is a one-off; the catalog's word for the account owner everywhere else is "dueño" (`es.ts:360` `ownerOnly`, `947` `forbiddenMessage`, `2505-2526` roles screen, `2628` `upgrade.askOwner`). Finding 1's fix removes the word entirely, which also resolves this — if the tech lead instead keeps some form of "ask the owner" wording, it must say "dueño", not "propietario".

## Checks
- [x] Only owned paths changed (confirmed by primary reviewer's diff; I re-read the same diff)
- [x] Nothing outside scope
- [x] Tests exercise the behavior; primary reviewer already proved the new tests fail on base code
- [x] en/es text present for every new key; tú form used throughout
- [ ] Copy says what happened and what to do next, and nothing false — **fails for `spendCap`**

## Optional notes (not blocking)
- `assistant.error.cantAnswer` ("I couldn't answer that. Try again." / "No pude responder eso. Inténtalo de nuevo.") is fine as the short line the card asked for.
- `credits_exhausted` reusing `upgrade.limit.aiCredits` verbatim is good — one consistent sentence for "AI credits used up" everywhere, and that string is out of this round's scope.
- Once the new string lands, the dash-prefixed test's two `toContain` assertions (`"today"`, `"credits"`) still pass unchanged against the replacement EN text above; no test edit needed.
