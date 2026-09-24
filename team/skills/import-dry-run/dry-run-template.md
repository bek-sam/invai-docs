# Dry run: <shop-slug>, YYYY-MM-DD

- **Build:** `git -C invai-backend log -1 --oneline` → <hash>
- **Files** (kept in `~/invai-pilots/<shop-slug>/raw/`): <file: channel, format, rows>
- **Readiness:** ready | ready with workarounds | blocked

## Numbers per channel
| Channel | Parse rate | Auto-map before rules | Auto-map after rules | Ship-by accuracy | Personalization read | Flags (overflow / too_long / suspicious / empty) |
|---|---|---|---|---|---|---|
| Etsy | 998/1000 (99.8%) | | | 20/20 | 19/20 | |

Re-import of the same file: <no duplicates / problem>.

## Misses
| # | Channel | What happened | Class (product / data / training) | Severity | Issue id | Evidence (scrubbed) |
|---|---|---|---|---|---|---|

## SKU rules added
| Pattern | Maps to | Items unblocked |
|---|---|---|

## Workarounds the shop needs
-

## Teardown
- [ ] Processes stopped  - [ ] MinIO files deleted (`mc rm --recursive --force local/invai-local/<companyId>/`; the listing after it is empty)  - [ ] Database dropped  - [ ] Redis DB flushed  - [ ] No raw files in git
