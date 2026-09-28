# Wave 20 QA acceptance tests (wave step 3, before T-20-1 and T-20-2 build)

| Field | Value |
|---|---|
| Owner | qa-engineer (sonnet) |
| Reviewed by | the feature owners (T-20-1 backend-engineer, T-20-2 web-engineer) when they start, plus reviewer at the card reviews |

## Owned paths (edit)
- `invai-backend/src/modules/{digest,market,today}/*.acceptance.test.ts` (new file `date-copy.acceptance.test.ts` preferred; extend existing ones only where needed)
- `invai-web/e2e/digest*.spec.ts`

## What to write
From T-20-1 AC1–AC5 and T-20-2 AC1–AC4 and the wording rule in `wave.md`:
- Backend, with a fixed clock of **2026-09-28** (a Monday) and a shop in America/Phoenix: a September-peak R1 item is not in Market watch or R1 output; an October-peak item still shows its act-by date; an in-progress peak uses "season is on now" (en/es); margin and on-time changes are points ("+6.9 pts" / "+6,9 pts"), zero is "unchanged" / "sin cambio"; mock `asOf` ≤ now and equals the end of the last complete ISO week; the Today overdue-label alert message contains no `T..:..:..` ISO pattern and shows "Sep 26".
- Web E2E (`e2e/digest.spec.ts` or a new `digest-dates.spec.ts`): Spanish digest heading has no English weekday or month; office@ on Settings → Notifications sees the translated no-access message; plan usage shows "10,000".
- Use margin 26.5 → 33.4 and on-time 95.0 → 97.5 in the fixture, so a relabelled relative change ("+26% pts") can't pass: expect "+6.9 pts" and "+2.5 pts" (architect A4: `build.ts:42-59` computes a relative `pctChange` for every glance metric today).
- The tests must fail now for the right reason (run them and paste the failures).

## Verification
- `pnpm typecheck && pnpm lint` in invai-backend and invai-web; the new tests run and fail for the stated reasons (own test DB `invai_t20_qa`, own API `PORT=3116` for E2E against a dev copy).
- Commit only these files. Don't push; only the tech lead pushes after the gate. Report: `invai-docs/waves/20/reports/QA-acceptance.md`.
