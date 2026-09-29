# Review of T-22-2 (round 1), tenancy co-review

- Reviewer: security-reviewer on opus. Author: backend-foundation on fable. Scope: tenancy only (migration/snapshot checks: reviewer r1).
- Verdict: **approve**

## Evidence I re-ran (git archive of invai-backend@6a8856c, DB `invai_t22_2s`, Redis DB 11; both dropped/flushed after)
| Command | Result |
|---|---|
| `vitest run --reporter=dot src/db src/modules/tenancy` | `Test Files 18 passed (18)`, `Tests 92 passed (92)` |
| `pg_constraint` count, FKs with `company_id` tables on both sides | 57 of 57 are two-column `(company_id, x) -> (company_id, id)` |
| Mutation: probe table with `order_id references orders(id)` + FK with swapped cols, re-run `fk-coverage.test.ts` | 2 failed: `zz_probe(order_id) -> orders(id)` flagged by both checks; swapped-column FK not flagged (note 2). Probe dropped. |
| As `invai_app`, `app.company_id` = shop B: `insert into designs(..., personalization_template_id = <shop A template>)` | **INSERTED**; template invisible to B (count 0). Rolled back. Recorded as S-39 (Low). |

## Focus questions
1. **User references.** FKs to `users`/`companies` stay single-column (global identity). No contract input carries a user id except `team.*` (`userId`), and those go through `getMember(tx, ctx.companyId, userId)` (NOT_FOUND for non-members, e.g. `setUserPin` service.ts:640-660); every `*By`/`actorUserId` write comes from the session (`ctx.actor`), grep `By: input.` finds only `floor-auth.ts` fed by the router's session user. No gap.
2. **New tables.** `fk-coverage.test.ts` introspects the migrated DB, so a new table's `.references(() => parent.id)` fails CI (proved above). It cannot see a reference column with no FK at all (see S-39).
3. **Cross-tenant insert without RLS**: present (`fk-coverage.test.ts`, `withSystem` insert of B `order_items` -> A order rejects `23503 order_items_order_id_fk`); passes.
4. **`updateOrg`**: `org.manage` (contract), covered by `authz.test.ts` matrix. Only the six named fields are copied into `settingsPatch`; `demo*`/`onboarding*` keys can't be set; JSON goes in as one bound parameter; top-level `||` merge keeps other keys. Zod bounds `transferAgeWarnDays` 1..365. Safe.
5. **S-26**: closed for FKs at invai-backend@3b50fb8 (49 FKs + 7 digest = 56 on the seeded copy, all validated); pending the tech lead's push. The residual (tenant references with **no** FK) is split out as S-39.

## Blocking findings
none (AC1 covers FKs; FK-less columns were never in the card).

## Checks
- [x] Only owned paths (tenancy scope) · [x] no tests weakened (`rls-coverage.test.ts` untouched) · [x] RLS coverage green · [x] S-26/S-39 recorded

## Optional notes (not blocking)
1. S-39 (Low, integrity): ~30 tenant reference columns have no FK (`order_items.{design,blank_variant,transfer,gang_sheet,shipment,bin,product}_id`, `designs.personalization_template_id`, `listing_*`, `reprints.*_transfer_id`, ...). `catalog.createDesign` stores `personalizationTemplateId` from input without a tenant load (service.ts:173). Reads stay isolated; keep "load foreign ids under the tenant" in `tenant-isolation-audit` step 4 until these are FKs.
2. Harden `fk-coverage`: require child `company_id` at the same position as the parent's, and flag tenant FKs on tables with nullable `company_id` (MATCH SIMPLE skips the check when it is NULL; today only webhook-event tables, which reference `companies`).
