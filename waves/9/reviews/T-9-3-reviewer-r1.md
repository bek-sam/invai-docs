# Review of T-9-3 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: imaging-engineer on Sonnet
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git worktree add ../invai-imaging-t93review 10c1aa2` (+contracts@2b2f12b, +backend@78a0e8f) | 3 worktrees, ownership matches card grants (`git diff --stat` vs prior commit: imaging `app/main.py`,`app/pdf.py`,`tests/test_pdf.py`,`tests/test_api.py`; contracts `src/schemas/vendors.ts`; backend `src/modules/vendors/service.ts`,`src/modules/vendors/invite.test.ts`) |
| `grep -rn "UserUnit"` across imaging worktree | Only in comments/docs/README and a pre-existing stale test (`tests/test_compose.py::test_long_sheet_pdf_uses_user_unit`, not touched by this card). No code path builds `/UserUnit` any more. |
| `uv run pytest tests/test_compose.py -k user_unit` at `10c1aa2` | FAILS — stale, unowned test still calls `write_image_pdf(...,300)` and now raises `ImageError`. Confirmed this is T-9-2's job to remove (report's own "coordination note"/"known gaps"); at current HEAD `6b9c8f3` the test is gone, replaced by a comment. |
| `uv run ruff check .` + `uv run pytest -q` at current imaging HEAD (`6b9c8f3`) | ruff clean; 51/51 passed |
| `.venv/bin/ruff check/format --check` on touched files, `pytest tests/test_pdf.py tests/test_api.py::test_compose_rejects_pdf_output_over_200in` at `10c1aa2` | clean; 5/5 passed |
| `node_modules/.bin/tsc --noEmit` in contracts@2b2f12b and backend@78a0e8f | both clean |
| createdb `invai_test_t93v`, `vitest run src/modules/vendors/invite.test.ts src/modules/vendors/vendors.test.ts` at backend@78a0e8f, DB dropped after | 9/9 passed |
| Copied `tests/test_pdf.py`+`tests/test_api.py` onto imaging base `bbb85a3` (no `.env` needed) | `ImportError: cannot import name 'PDF_MAX_LENGTH_IN'` — new tests cannot even collect without the change |
| Copied `invite.test.ts` onto backend base `f3b0eea`, ran against a scratch DB (dropped after) | 2/3 new tests FAIL on base ("rejects...at invite", "rejects switching...on update"); the exactly-200 accept test passes on base too (expected, base had no cap) |
| `scan-test-weakening.sh` on imaging/contracts/backend worktrees vs their prior commit | no hits in any repo |
| `grep -rn "\.spec\b"` for all writers of `vendorConnections.spec` in backend | only `inviteVendor` (insert) and `updateConnection` (update) write it; both call `sheetSpecPdfCapError`. `resolveVendor`/`sheets.ts` and the two other `.update(vendorConnections)` calls (`clearDefault`, `activatePending`) never touch `spec`. Seed (`db/seed/builder.ts`) writes fixture data directly, outside runtime validation, as expected. |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. PDF sheets >200in rejected at spec save; PNG unaffected; decision recorded | Yes | `wave.md`/card record cap-not-split decision. `sheetSpecPdfCapError` (contracts) checked in both backend writers; `app/pdf.py` raises `ImageError` above 200in regardless of caller; `ComposeRequest._pdf_length_cap` only fires when `pdf_key is not None`; `test_api.py`'s new test explicitly proves a 240in PNG-only compose still returns 200 |
| 2. 240in sheet split-or-rejected with test coverage (page count/size or error) | Yes | `test_sheet_over_200in_is_rejected`/`test_wide_sheet_over_200in_is_also_rejected` (imaging), `test_compose_rejects_pdf_output_over_200in` (422+detail check), backend invite/update tests at 240in — all assert the `ImageError`/`BAD_REQUEST` |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat`) — matches wave.md's file-ownership matrix and grants exactly
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened (no `.skip`, loosened assertions, mocks of the unit under test, rewritten snapshots) — scan clean, and the new tests fail without the change (see evidence)
- [x] Tenancy (`withTenant`, RLS on new tables), idempotency, money in cents, en/es text — n/a: no new tables, no money fields, no side effects; spec-save checks run inside the existing `withTenant`/tx in both writers
- [x] Decisions recorded where needed — cap-not-split decision and rationale recorded in `wave.md` and the card

## Optional notes (not blocking)
- At the exact commit `10c1aa2`, the full imaging suite has one failing test (`test_long_sheet_pdf_uses_user_unit` in `tests/test_compose.py`) because that file wasn't touched by this card in the shared working tree — the author's report discloses this explicitly and it's fixed by T-9-2's very next commit (`6b9c8f3`, where HEAD's `uv run pytest` is 51/51 green). Worth tightening the parallel-batch protocol (agent-brief) so a card that removes a still-referenced behavior always leaves a green suite at its own commit, even mid-batch.
- `README.md:57` in invai-imaging still describes the old `/UserUnit` fallback for PDF pages over 200in; stale doc, not in this card's owned/granted paths, harmless but worth a follow-up ticket.
