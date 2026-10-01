# T-P1-5: Floor QC result banner says what happened, in Spanish too (B-222)

| Field | Value |
|---|---|
| Wave | P1 |
| Scope ref | `always-in-scope: bug` (B-222, Medium) |
| Spec | backlog B-222; source `waves/A1/reports/gate-screens-qa.md` |
| Owner | floor-engineer |
| Reviewer | reviewer (opus) |
| Co-reviewers | none (copy fix on an existing screen) |
| Risk flags | ui (copy only) |
| Model | sonnet |

## Owned paths (edit)
- `invai-floor/src/stations/QcStation.tsx` (+ its test), `invai-floor/src/i18n/en.ts`, `invai-floor/src/i18n/es.ts`

## Read-only paths
- Everything else.

## Acceptance criteria
1. After a QC pass, the result banner heading is a past-tense result ("Passed" / "Aprobado"), not the button label "APROBAR" (`QcStation.tsx:~145` uses the button key `floor.qc.pass`). Same check for the fail/reprint result ("Failed" or the existing wording / "Rechazado"), so neither result reuses a button key.
2. The banner still shows the order number line, and pass and fail look and sound different (`build-floor-flow`).
3. New keys exist in en and es (`es.ts` is typed from `en.ts`, so typecheck catches a missing key); plain-language, tú form.
4. A unit test asserts the result heading uses the result key, in es.

## Verification
- `cd invai-floor && pnpm typecheck && pnpm lint && pnpm test && pnpm build 2>&1 | tail -n 20`
- One floor pass at 1280×800 in Spanish through QC pass (dev floor on 5174 or your own Vite port against the API on :3000 if it's up; don't reseed). One screenshot, looked at.

## Out of scope
- Other stations' copy, the web app.

## Budget
- About 45 minutes.

Commit only your paths. Don't push. Report: `invai-docs/waves/P1/reports/T-P1-5.md`.
